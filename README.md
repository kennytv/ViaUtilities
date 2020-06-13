# ViaUtilities
Various automated utility tools for Via updates.

## Usage
- `py version-checker.py` is the main file, subsequently calling the other scripts. It searches for new snapshots and releases. Once one is found, the server will be downloaded its mappings will be generated.
  - Use `--generateSources` to also generate mapped sources for client and server. 
  - Use `--noMinimize` to **not** remove libs/unneeded assets from the client and server jar.
  - Use `--ver <version>` to generate mappings/sources for a specific, older version 
- `./generate-sources.sh <client/server> <version>` to generate client and server sources with Mojang mappings.
  - Requires an enigma cli jar in the main directory called `enigma-cli.jar`.
  - Requires the proguard mapping file `sources/<platform>-<version>.txt` (e.g. `sources/client-1.15.2.txt`)
- `./burger.sh <old version> <new version>` to generate Burger a diff
  - Requires the client jar in `versions/client-<version>.jar` (e.g. `versions/client-1.15.2.jar`)
-  `java -jar MappingsGenerator-1.0.jar <path to server jar> <version>`

Burger mapping files and Vitrine html views will be saved in the `Burger` directory, Via mappings in the `mappings directly`. If sources are exported, they will be thrown into the `sources` dir.