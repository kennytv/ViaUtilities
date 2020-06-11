## TODO
- [ ] Automatically find Enigma jar instead of manually setting its path
- [ ] Wait and post Minecraft news articles if possible (?)

## Usage
- `py version-checker.py` to search for new snapshots and releases. Once one is found, the server will be downloaded its mappings will be generated.
- `./generate-sources.sh <client/server> <version>` to generate client and server sources with Mojang mappings by the version currently set in the `versions.txt` file. **Needs an enigma jar in the main directory called `enigma-cli.jar`.**
- `./burger.sh <old version> <new version>` to generate Burger a diff
-  `java -jar MappingsGenerator-1.0.jar <path to server jar> <version>`

Running the version-checker will automatically generate mappings with the MappingsGenerator. To also generate server and client sources with it, add `--generateSources` when calling the version-checker Python script.