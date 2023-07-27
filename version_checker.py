import time

import six.moves.urllib.request
import json
import wget
import subprocess
import os
from git import Repo
from lib import args

MANIFEST_URL = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"


def get_json_from_url(url: str):
    with six.moves.urllib.request.urlopen(url) as stream:
        return json.load(stream)


def delete(path: str):
    try:
        os.remove(path)
    except:
        pass


def save_to_versions_file(release: str, snapshot: str):
    with open("versions.txt", "w") as versions_file:
        versions_file.write(release + "\n")
        versions_file.write(snapshot)


def push(message: str):
    repo = Repo("")
    repo.git.add(update=True)
    repo.index.commit(message)
    origin = repo.remote(name='origin')
    origin.push()


def process_mappings(json_object, old_version: str, version: str):
    client_url: str = json_object["downloads"]["client"]["url"]
    server_url: str = json_object["downloads"]["server"]["url"]

    if not os.path.isdir("versions"):
        os.mkdir("versions")

    # Client jar download
    client_file_path: str = "versions/client-" + version + ".jar"
    if os.path.isfile(client_file_path):
        print("Client file already present!")
    else:
        print("=== Downloading client from " + client_url + "...", flush=True)
        wget.download(client_url, client_file_path)

    # Server jar download
    server_file = "versions/server-" + version + ".jar"
    if os.path.isfile(server_file):
        print("Server file already present!")
    else:
        print("\n=== Downloading server...", flush=True)
        wget.download(server_url, server_file)

    # Read old and next version for Via mapping file names
    with open("next_release.txt", 'r') as versionFile:
        next_release: str = versionFile.read()
    with open("versions.txt", 'r') as versionsFile:
        old_release: str = versionsFile.read().split("\n")[0]

    # Run Via mappings gen
    print("\n=== Running mappings generator...\n", flush=True)
    os.system(".\\prepare-mappings-generator.sh " + version)
    os.chdir("Mappings")
    subprocess.call(["java", "-jar", "MappingsGenerator.jar", "server.jar", next_release])
    subprocess.call(
        ["java", "-cp", "MappingsGenerator.jar", "com.viaversion.mappingsgenerator.MappingsOptimizer", old_release,
         next_release, "--generateDiffStubs"])
    subprocess.call(
        ["java", "-cp", "MappingsGenerator.jar", "com.viaversion.mappingsgenerator.MappingsOptimizer", next_release,
         old_release, "--generateDiffStubs"])

    # Save processed version and push
    with open("last_snapshot.txt", 'w') as versionFile:
        versionFile.write(version)

    try:
        push("Update: " + version)
    except:
        print("Error pushing changes to the Mappings repo :(")

    os.chdir("..")

    # Run Burger
    vitrine_file = "Burger\\vitrine\\{0}_{1}.html".format(old_version, version)
    if old_version == version:
        # Only dump the one version
        if not os.path.isfile("Burger\\out\\" + version + ".json"):
            os.system(".\\burger.sh " + version)
    elif os.path.isfile(vitrine_file):
        print("Burger/Vitrine file already present!")
    else:
        print("\n=== Generating Burger mapping diff...\n", flush=True)
        os.system(".\\burger.sh {0} {1}".format(old_version, version))
        os.system(".\\" + vitrine_file)

    # Decompile and deobfuscate vanilla jars
    if args.hasArg("generateSources", 'v'):
        print("\n=== Decompiling sources with VanillaGradle...\n", flush=True)
        os.system("py sources.py --decompile --push --ver " + version)
        os.system("py diff_checker.py --output diffs/" + version + ".patch")

    # Keep this as a backup just in case
    if args.hasArg("generateSourcesEnigma"):
        print("\n=== Generating sources with Enigma...\n", flush=True)
        client_mappings_url: str = json_object["downloads"]["client_mappings"]["url"]
        server_mappings_url: str = json_object["downloads"]["server_mappings"]["url"]
        if not os.path.isdir("sources"):
            os.mkdir("sources")

        print("\nGenerating client sources...\n", flush=True)
        wget.download(client_mappings_url, "sources/client-" + version + ".txt")
        os.system(".\\sources-enigma.sh client " + version)

        # print("\nGenerating server sources...\n", flush=True)
        # wget.download(server_mappings_url, "sources/server-" + version + ".txt")
        # os.system(".\\sources-enigma.sh server " + version)

    print("\nFinished", version, "processing!", flush=True)


def download_and_process_mappings(old_version: str, version: str, url: str):
    if old_version == "":
        old_version = version

    json_object = get_json_from_url(url)

    with open("versions/" + version + ".json", 'w') as version_file:
        json.dump(json_object, version_file)

    process_mappings(json_object, old_version, version)


def check():
    attempt: int = 0
    while True:
        attempt += 1
        print("Checking #" + str(attempt), flush=True)

        json_object = get_json_from_url(MANIFEST_URL)
        latest = json_object["latest"]
        latest_release: str = latest["release"]
        latest_snapshot: str = latest["snapshot"]

        # Load last versions from file
        try:
            with open("versions.txt", "r") as versions_file:
                old_versions: list[str] = versions_file.read().split("\n")
            old_release: str = old_versions[0]
            old_snapshot: str = old_versions[1]
        except IOError:
            old_release = latest_release
            old_snapshot = latest_snapshot
            save_to_versions_file(old_release, latest_snapshot)

        # Check for a new release or snapshot
        if old_release != latest_release:
            print("A new release has been published:", latest_release, flush=True)
            old: str = old_release
            new: str = latest_release
            save_to_versions_file(latest_release, old_snapshot)
        elif old_snapshot != latest_snapshot:
            print("A new snapshot has been published:", latest_snapshot, flush=True)
            old: str = old_snapshot
            new: str = latest_snapshot
            save_to_versions_file(old_release, latest_snapshot)
        else:
            time.sleep(20)
            continue

        # Look for version data of the new release
        version_data = None
        for entry in json_object["versions"]:
            if entry["id"] == new:
                version_data = entry
                break

        if version_data is None:
            print("VERSION DATA FOR", new, "NOT FOUND!", flush=True)
        else:
            download_and_process_mappings(old, new, version_data["url"])

        print("Resetting attempt count, resuming search in 5 minutes", flush=True)
        attempt = 0
        time.sleep(300)


if __name__ == "__main__":
    ver: str | None = args.getArg("ver")
    if ver is not None and args.hasArg("localVersionFile", 'l'):
        # Process version from local version data
        with open("versions/" + ver + ".json", 'r') as file:
            jsonObject = json.load(file)
        process_mappings(jsonObject, args.getArg("oldVer"), ver)
    elif ver is not None:
        # Generate for a single given version
        print("Generating data for " + ver)
        for entry in get_json_from_url(MANIFEST_URL)["versions"]:
            if entry["id"] == ver:
                download_and_process_mappings(ver, ver, entry["url"])
                break

        print("Version not found in Mojang version manifest")
    else:
        # Start check task
        check()
