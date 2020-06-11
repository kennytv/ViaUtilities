## TODO
- [] Include Burger update.sh and directory in this git repo
- [] Automatically find Enigma jar instead of manually setting its path
- [] Throw mappings into a mapping directory

## Usage
- `py version-checker.py` to search for new snapshots and releases. Once one is found, the server will be downloaded its mappings will be generated.
- `./enigma.sh` to generate client and server sources with Mojang mappings by the version currently set in the `versions.txt` file. **Needs an enigma jar in the main directory.**