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

```
wget https://mediafilez.forgecdn.net/files/4048/412/Decorations+Modpack+(Forge)+1.19.2+-+v5.zip
unzip Decorations+Modpack+(Forge)+1.19.2+-+v5.zip
cd mods
wget https://mediafilez.forgecdn.net/files/3871/432/SereneSeasons-1.19-8.0.0.19.jar
```

3) start service

```
docker-compose up -d minecraft
```

client quick-start
------------------

Ensure you download the same mod for your client and that the client is running Forge.

```
wget https://maven.minecraftforge.net/net/minecraftforge/forge/1.19.2-43.1.52/forge-1.19.2-43.1.52-installer.jar
java -jar forge-1.19.2-43.1.52-installer.jar
# click OK and Install Client
cd ~/.minecraft/
wget https://mediafilez.forgecdn.net/files/4048/412/Decorations+Modpack+(Forge)+1.19.2+-+v5.zip
unzip Decorations+Modpack+(Forge)+1.19.2+-+v5.zip
cd mods
wget https://mediafilez.forgecdn.net/files/3871/432/SereneSeasons-1.19-8.0.0.19.jar
```

backups
-------
```
docker-compose up backup
```

The backup file should be in backups with a timestamp.
