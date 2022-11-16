minecraft mod server
--------------------

Everything you need to start a minecraft server with mods.


server quick-start
------------------

1) Install dependencies
```
apt install python3-pip docker.io
pip3 install docker-compose
```

Ensure you can run docker-compose as a normal user, otherwise run as sudo.

2) download mods

Download the zip file from: https://www.curseforge.com/minecraft/modpacks/decorations-modpack-forge/files/4048412
Place this file into modpacks/decorations.zip

3) start service

```
docker-compose up -d
```

client quick-start
------------------

Ensure you download the same mod for your client and that the client is running Forge.

TODO: better instructions here

backups
-------
```
docker-compose up backup
```

The backup file should be in backups.
