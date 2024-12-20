# ViaUtilities
Various automated utility tools for Via updates. Some data may be exclusive to the gh-pages branch.

## Dependencies
* At least Java 17
* Python with six, jawa, and wget packages
* GitPython
* (git) bash

## Preparation
Run `git submodule update --init`

## Usage
- `py version_checker.py` is the main file, subsequently calling the other scripts. It searches for new snapshots and releases. Once one is found, the server will be downloaded its mappings will be generated.
  - `--generateSources` or `-v` to generate sources using VanillaGradle (using the sources script you'll have to hand edit)
  - `--generateSourcesEnigma` to also generate mapped sources for client and server - I don't actually use this anymore and only keep it as a fallback; [VanillaGradle is where it's at](https://github.com/SpongePowered/VanillaGradle)
  - `--ver <version>` to generate mappings/sources for a specific, older version.
  - `--localVersionFile` or `-l` to use a version manifest from the version directory instead of downloading it (also need `--oldVer <old version>`)
- `./sources-enigma.sh <client/server> <version>` to generate client and server sources with Mojang mappings.
  - Requires an enigma cli jar in the main directory called `enigma-cli.jar`.
  - Requires the proguard mapping file `sources/<platform>-<version>.txt` (e.g. `sources/client-1.15.2.txt`)
- `./burger.sh <old version> <new version>` to generate Burger a diff.
  - Requires the client jar in `versions/client-<version>.jar` (e.g. `versions/client-1.15.2.jar`).
- `py sources.py` to generate and export sources using VanillaGradle
  - `--ver` (required)
  - `--fromCache` or `-c`to not move the version manifest to the project root
  - `--decompile` or `-d` to decompile the version
  - `--push` or `-p` to commit and push the changes to the project's remote
  - Example: `py sources.py --ver 1.18.2 -d -p`
- `diff_checker.py` is basically Burger lite but operating on mapped code for things outside dumpable registries
  - `--output <path>` (required) output file path for the generated (kind of) patch file
- See https://github.com/ViaVersion/Mappings on how to use the mappings generator

Burger mapping files and Vitrine html views will be saved in the `Burger` directory, Via mappings in the `mappings directly`. If sources are exported, they will be thrown into the `sources` dir.

## License
This project is licensed under the [GNU General Public License 3.0](https://github.com/KennyTV/ViaUtilities/blob/master/LICENSE).

The tree contains a pre-compiled, cherry-picked [Enigma](https://github.com/FabricMC/Enigma/) ([GNU Lesser General Public License](https://github.com/FabricMC/Enigma/blob/master/LICENSE)) version, since it likes to break every now and then.
You can find the modified source [here](https://github.com/KennyTV/Enigma).
