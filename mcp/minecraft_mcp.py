#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["mcp>=1.2.0"]
# ///
"""Minecraft MCP server.

Exposes a running Minecraft server (anything that speaks the Source RCON
protocol, e.g. itzg/minecraft-server with ENABLE_RCON=true) to Claude as a set
of MCP tools. Run via `uv run mcp/minecraft_mcp.py` -- uv installs the single
`mcp` dependency automatically from the inline metadata above.

Connection is configured by environment variables:
  RCON_HOST      default 127.0.0.1
  RCON_PORT      default 25575
  RCON_PASSWORD  default "minecraft"
"""

from __future__ import annotations

import os
import socket
import struct

from pathlib import Path

from mcp.server.fastmcp import FastMCP


def _load_env_file() -> dict[str, str]:
    """Read the repo .env (one dir up) so RCON_PASSWORD works without exporting it.

    Real environment variables take precedence over .env values.
    """
    values: dict[str, str] = {}
    env_path = Path(__file__).resolve().parent.parent / ".env"
    try:
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            values[key.strip()] = val.strip().strip('"').strip("'")
    except OSError:
        pass
    return values


_ENV_FILE = _load_env_file()


def _conf(name: str, default: str) -> str:
    value = os.environ.get(name) or _ENV_FILE.get(name)
    return value if value else default


RCON_HOST = _conf("RCON_HOST", "127.0.0.1")
RCON_PORT = int(_conf("RCON_PORT", "25575"))
RCON_PASSWORD = _conf("RCON_PASSWORD", "minecraft")
RCON_TIMEOUT = float(os.environ.get("RCON_TIMEOUT", "5"))

# Source RCON packet types.
_SERVERDATA_AUTH = 3
_SERVERDATA_EXECCOMMAND = 2
_SERVERDATA_RESPONSE_VALUE = 0


class RconError(RuntimeError):
    """Raised when an RCON connection, auth, or command fails."""


def _send_packet(sock: socket.socket, req_id: int, ptype: int, body: str) -> None:
    payload = struct.pack("<ii", req_id, ptype) + body.encode("utf-8") + b"\x00\x00"
    sock.sendall(struct.pack("<i", len(payload)) + payload)


def _recv_exact(sock: socket.socket, n: int) -> bytes:
    chunks = []
    remaining = n
    while remaining > 0:
        chunk = sock.recv(remaining)
        if not chunk:
            raise RconError("RCON connection closed unexpectedly")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def _recv_packet(sock: socket.socket) -> tuple[int, int, str]:
    (length,) = struct.unpack("<i", _recv_exact(sock, 4))
    data = _recv_exact(sock, length)
    req_id, ptype = struct.unpack("<ii", data[:8])
    body = data[8:-2].decode("utf-8", errors="replace")
    return req_id, ptype, body


def rcon_command(command: str) -> str:
    """Open a short-lived RCON connection, authenticate, run one command."""
    try:
        with socket.create_connection((RCON_HOST, RCON_PORT), timeout=RCON_TIMEOUT) as sock:
            sock.settimeout(RCON_TIMEOUT)

            _send_packet(sock, 1, _SERVERDATA_AUTH, RCON_PASSWORD)
            resp_id, _, _ = _recv_packet(sock)
            if resp_id == -1:
                raise RconError("RCON authentication failed (check RCON_PASSWORD)")

            _send_packet(sock, 2, _SERVERDATA_EXECCOMMAND, command)
            _, _, body = _recv_packet(sock)
            return body.strip()
    except OSError as exc:
        raise RconError(
            f"Could not reach RCON at {RCON_HOST}:{RCON_PORT} ({exc}). "
            "Is the server running with ENABLE_RCON=true?"
        ) from exc


mcp = FastMCP("minecraft")


@mcp.tool()
def run_command(command: str) -> str:
    """Run an arbitrary Minecraft server command via RCON and return its output.

    Pass the command without a leading slash, e.g. "time set day" or
    "difficulty hard". This is the general escape hatch for anything the
    dedicated tools below don't cover.
    """
    return rcon_command(command) or "(no output)"


@mcp.tool()
def list_players() -> str:
    """List players currently online (wraps the `list` command)."""
    return rcon_command("list")


@mcp.tool()
def say(message: str) -> str:
    """Broadcast a chat message to everyone on the server."""
    return rcon_command(f"say {message}") or f"Broadcast: {message}"


@mcp.tool()
def give(player: str, item: str, count: int = 1) -> str:
    """Give a player an item, e.g. give("Steve", "minecraft:diamond", 10)."""
    return rcon_command(f"give {player} {item} {count}")


@mcp.tool()
def teleport(player: str, target: str) -> str:
    """Teleport a player to another player or to "x y z" coordinates."""
    return rcon_command(f"tp {player} {target}")


@mcp.tool()
def set_time(value: str) -> str:
    """Set the world time. Accepts day, night, noon, midnight, or a tick number."""
    return rcon_command(f"time set {value}")


@mcp.tool()
def set_weather(weather: str, duration: int | None = None) -> str:
    """Set weather to clear, rain, or thunder (optional duration in seconds)."""
    cmd = f"weather {weather}"
    if duration is not None:
        cmd += f" {duration}"
    return rcon_command(cmd)


@mcp.tool()
def gamemode(player: str, mode: str) -> str:
    """Set a player's game mode: survival, creative, adventure, or spectator."""
    return rcon_command(f"gamemode {mode} {player}")


# --- Building / world editing --------------------------------------------------
# RCON commands run from the server console, which has no player position, so use
# ABSOLUTE coordinates. Relative (~) and local (^) coordinates resolve to 0 here.


@mcp.tool()
def set_block(x: int, y: int, z: int, block: str, mode: str = "replace") -> str:
    """Place a single block at absolute x/y/z.

    block is a block id like "minecraft:gold_block", optionally with block
    states, e.g. "minecraft:oak_stairs[facing=east]". mode is one of
    replace, destroy, or keep.
    """
    return rcon_command(f"setblock {x} {y} {z} {block} {mode}") or "(block placed)"


@mcp.tool()
def fill(
    x1: int, y1: int, z1: int,
    x2: int, y2: int, z2: int,
    block: str,
    mode: str = "replace",
) -> str:
    """Fill the cuboid between two absolute corners with a block.

    Great for walls, floors, and clearing areas (use "minecraft:air").
    mode is one of replace, destroy, keep, hollow, or outline. The region is
    capped at 32768 blocks by the server.
    """
    return rcon_command(f"fill {x1} {y1} {z1} {x2} {y2} {z2} {block} {mode}")


@mcp.tool()
def clone(
    x1: int, y1: int, z1: int,
    x2: int, y2: int, z2: int,
    dx: int, dy: int, dz: int,
) -> str:
    """Copy the cuboid (x1..x2) to a new region whose lowest corner is dx/dy/dz."""
    return rcon_command(f"clone {x1} {y1} {z1} {x2} {y2} {z2} {dx} {dy} {dz}")


@mcp.tool()
def summon(entity: str, x: int, y: int, z: int, nbt: str = "") -> str:
    """Summon an entity (e.g. "minecraft:armor_stand") at absolute x/y/z.

    nbt is an optional NBT tag string, e.g. '{NoGravity:1b}'.
    """
    cmd = f"summon {entity} {x} {y} {z}"
    if nbt:
        cmd += f" {nbt}"
    return rcon_command(cmd) or "(entity summoned)"


@mcp.resource("server://status")
def server_status() -> str:
    """Current server status (online player list)."""
    try:
        return rcon_command("list")
    except RconError as exc:
        return f"Server unreachable: {exc}"


if __name__ == "__main__":
    mcp.run()
