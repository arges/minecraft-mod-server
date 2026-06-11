# Minecraft server

A vanilla Minecraft server you can run with one command — and control from Claude.

- **Vanilla Minecraft** (latest stable), running in Docker via [`itzg/minecraft-server`](https://github.com/itzg/docker-minecraft-server).
- An **MCP server** lets Claude run in-game commands over RCON — list players, give items, change time/weather, teleport, place/fill blocks, and more, all in natural language.

## Requirements

- Docker with Compose v2 (`docker compose`).
- [`uv`](https://docs.astral.sh/uv/) (only for the Claude/MCP integration).

## Server quick start

1. Configure the RCON password:

   ```bash
   cp .env.example .env
   # edit .env: set a strong RCON_PASSWORD (letters + digits)
   ```

2. Start the server:

   ```bash
   docker compose up -d minecraft
   docker compose logs -f minecraft   # watch until you see "Done ... For help, type help"
   ```

The server listens on `25565`. RCON listens on `127.0.0.1:25575` only (used by the MCP server below).

### Pinning a version

`VERSION: "LATEST"` in `docker-compose.yml` tracks the newest stable release. To lock clients and
server to a specific version, set e.g. `VERSION: "1.21.4"`.

### Console access

```bash
docker attach minecraft   # detach with Ctrl-p Ctrl-q
```

## Client quick start

In the Minecraft launcher, pick the **same version** as the server (whatever `LATEST` resolved to,
or your pinned `VERSION`), then **Multiplayer → Add Server** and point it at the server's address
(`localhost` if it's the same machine).

## Control the server from Claude

This repo ships an MCP server (`mcp/minecraft_mcp.py`) wired up in `.mcp.json`, so Claude Code
picks it up automatically when you open the project (you'll be prompted to trust it the first time).

**Prerequisites:** the Minecraft server running (above) and [`uv`](https://docs.astral.sh/uv/)
installed. `uv` runs the MCP server and installs its one dependency on demand — no venv needed.
The MCP server reads `RCON_PASSWORD` straight from `.env`, so there's nothing else to configure.

In Claude Code, check it's connected:

```
/mcp
```

You should see the **minecraft** server listed. Now just ask, e.g.:

- "Who's online right now?"
- "Give Steve 10 diamonds."
- "Set the time to day and make the weather clear."
- "Teleport Alex to Steve."
- "Build a 10x10 stone platform at y=70 around x=100, z=100."
- "Run the command `difficulty hard`."

### Tools exposed

| Tool | What it does |
|------|--------------|
| `run_command` | Run any server command (the general escape hatch) |
| `list_players` | List online players |
| `say` | Broadcast a chat message |
| `give` | Give a player items |
| `teleport` | Teleport a player to another player or coordinates |
| `set_time` | Set world time (day/night/noon/midnight or ticks) |
| `set_weather` | Set weather (clear/rain/thunder) |
| `gamemode` | Change a player's game mode |
| `set_block` | Place a single block at x/y/z |
| `fill` | Fill a cuboid with a block (walls, floors, clearing) |
| `clone` | Copy a region to another location |
| `summon` | Summon an entity at x/y/z |

> Building tools use **absolute** coordinates — RCON runs from the server console, which has no
> player position, so relative (`~`) coordinates resolve to 0.

No `uv`? Use pip instead and point your MCP client at `python3 mcp/minecraft_mcp.py`:

```bash
python3 -m venv .venv && . .venv/bin/activate && pip install -r mcp/requirements.txt
```

## Backups

```bash
docker compose run --rm backup
```

Writes a timestamped `data-YYYYmmddHHMMSS.tar.bz2` into `backup/`.

## Security notes

- RCON is bound to `127.0.0.1` only. **Never** map port `25575` publicly.
- Always set a strong `RCON_PASSWORD` — anyone who can reach RCON has full server control.
- `.env` is git-ignored; keep your RCON password out of commits.
