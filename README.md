# ViaUtilities
Various automated utility tools for Via updates.

## Usage
- `py version-checker.py` is the main file, subsequently calling the other scripts. It searches for new snapshots and releases. Once one is found, the server will be downloaded its mappings will be generated. Use the `--generateSources` flag to also generate mapped sources for client and server.
- `./generate-sources.sh <client/server> <version>` to generate client and server sources with Mojang mappings by the version currently set in the `versions.txt` file. **Needs an enigma jar in the main directory called `enigma-cli.jar`.**
- `./burger.sh <old version> <new version>` to generate Burger a diff
-  `java -jar MappingsGenerator-1.0.jar <path to server jar> <version>`

Burger mapping files and Vitrine html views will be saved in the `Burger` directory, Via mappings in the `mappings directly`. If sources are exported, they will be thrown into the `sources` dir.