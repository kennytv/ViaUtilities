import time

import six.moves.urllib.request
import json
import wget
import subprocess
import os
from git import Repo
from lib import args


def loadJson(url: str):
    with six.moves.urllib.request.urlopen(url) as stream:
        return json.load(stream)


def delete(path: str):
    try:
        os.remove(path)
    except:
        pass


def saveToFile(release: str, snapshot: str):
    versionsFile = open("versions.txt", "w")
    versionsFile.write(release + "\n")
    versionsFile.write(snapshot)
    versionsFile.close()


def push(message: str):
    repo = Repo("")
    repo.git.add(update=True)
    repo.index.commit(message)
    origin = repo.remote(name='origin')
    origin.push()


def processMappings(jsonObject, oldVersion: str, version: str):
    clientUrl: str = jsonObject["downloads"]["client"]["url"]
    serverUrl: str = jsonObject["downloads"]["server"]["url"]

    if not os.path.isdir("versions"):
        os.mkdir("versions")

    # Client download
    clientFilePath: str = "versions/client-" + version + ".jar"
    if os.path.isfile(clientFilePath):
        print("Client file already present!")
    else:
        print("=== Downloading client from " + clientUrl + "...", flush=True)
        wget.download(clientUrl, clientFilePath)

    # Server download
    serverFile = "versions/server-" + version + ".jar"
    if os.path.isfile(serverFile):
        print("Server file already present!")
    else:
        print("\n=== Downloading server...", flush=True)
        wget.download(serverUrl, serverFile)

    # Via mappings
    with open("next_release.txt", 'r') as versionsFile:
        nextRelease: str = versionsFile.read()
    with open("versions.txt", "r") as versionsFile:
        oldRelease: str = versionsFile.read().split("\n")[0]

    print("\n=== Running mappings generator...\n", flush=True)
    os.system(".\\prepare-mappings-generator.sh " + version)
    os.chdir("Mappings")
    subprocess.call(["java", "-jar", "MappingsGenerator.jar", "server.jar", nextRelease])
    subprocess.call(
        ["java", "-cp", "MappingsGenerator.jar", "com.viaversion.mappingsgenerator.MappingsOptimizer", oldRelease,
         nextRelease, "--generateDiffStubs"])
    subprocess.call(
        ["java", "-cp", "MappingsGenerator.jar", "com.viaversion.mappingsgenerator.MappingsOptimizer", nextRelease,
         oldRelease, "--generateDiffStubs"])

    try:
        push("Update: " + version)
    except:
        print("Error pushing changes to the Mappings repo :(")

    os.chdir("..")

    # Burger
    vitrineFile = "Burger\\vitrine\\{0}_{1}.html".format(oldVersion, version)
    if oldVersion == version:
        # Only dump the one version
        if not os.path.isfile("Burger\\out\\" + version + ".json"):
            os.system(".\\burger.sh " + version)
    elif os.path.isfile(vitrineFile):
        print("Burger/Vitrine file already present!")
    else:
        print("\n=== Generating Burger mapping diff...\n", flush=True)
        os.system(".\\burger.sh {0} {1}".format(oldVersion, version))
        os.system(".\\" + vitrineFile)

    # Sources export
    if args.hasArg("generateSources", 'v'):
        print("\n=== Decompiling sources with VanillaGradle...\n", flush=True)
        os.system("py sources.py --decompile --push --ver " + version)
        os.system("py diff-checker.py --output diffs/" + version + ".patch")

    if args.hasArg("generateSourcesEnigma"):
        print("\n=== Generating sources with Enigma...\n", flush=True)
        clientMappingsUrl: str = jsonObject["downloads"]["client_mappings"]["url"]
        serverMappingsUrl: str = jsonObject["downloads"]["server_mappings"]["url"]
        if not os.path.isdir("sources"):
            os.mkdir("sources")

        print("\nGenerating client sources...\n", flush=True)
        wget.download(clientMappingsUrl, "sources/client-" + version + ".txt")
        os.system(".\\sources-enigma.sh client " + version)

        # print("\nGenerating server sources...\n", flush=True)
        # wget.download(serverMappingsUrl, "sources/server-" + version + ".txt")
        # os.system(".\\sources-enigma.sh server " + version)

    print("\nFinished", version, "processing!", flush=True)


def downloadMappings(oldVersion: str, version: str, url: str):
    if oldVersion == "":
        oldVersion = version

    jsonObject = loadJson(url)

    with open("versions/" + version + ".json", 'w') as file:
        json.dump(jsonObject, file)

    processMappings(jsonObject, oldVersion, version)


def check():
    attempt: int = 0
    while True:
        attempt += 1
        print("Checking #" + str(attempt), flush=True)

        jsonObject = loadJson("https://piston-meta.mojang.com/mc/game/version_manifest_v2.json")

        latest = jsonObject["latest"]
        latestRelease: str = latest["release"]
        latestSnapshot: str = latest["snapshot"]

        # Load last versions from file
        try:
            with open("versions.txt", "r") as versionsFile:
                oldVersions: list[str] = versionsFile.read().split("\n")
            oldRelease: str = oldVersions[0]
            oldSnapshot: str = oldVersions[1]
        except IOError:
            oldRelease = latestRelease
            oldSnapshot = latestSnapshot
            saveToFile(oldRelease, latestSnapshot)

        # Check for a new release or snapshot
        if oldRelease != latestRelease:
            print("A new release has been published:", latestRelease, flush=True)
            old: str = oldRelease
            new: str = latestRelease
            oldRelease: str = latestRelease

            saveToFile(latestRelease, oldSnapshot)
        elif oldSnapshot != latestSnapshot:
            print("A new snapshot has been published:", latestSnapshot, flush=True)
            old: str = oldSnapshot
            new: str = latestSnapshot
            oldSnapshot: str = latestSnapshot

            saveToFile(oldRelease, latestSnapshot)
        else:
            time.sleep(20)
            continue

        # Look for version data of the new release
        versionData = None
        for entry in jsonObject["versions"]:
            if entry["id"] == new:
                versionData = entry
                break

        if versionData is None:
            print("VERSION DATA FOR", new, "NOT FOUND!", flush=True)
        else:
            downloadMappings(old, new, versionData["url"])

        print("Resetting attempt count, resuming search in 5 minutes", flush=True)
        attempt = 0
        time.sleep(300)


if __name__ == "__main__":
    ver: str | None = args.getArg("ver")
    if ver is not None and args.hasArg("localVersionFile", 'l'):
        with open("versions/" + ver + ".json", 'r') as file:
            jsonObject = json.load(file)
        processMappings(jsonObject, args.getArg("oldVer"), ver)
    elif ver is not None:
        # Generate for a single given version
        print("Generating data for " + ver)
        for entry in loadJson("https://piston-meta.mojang.com/mc/game/version_manifest_v2.json")["versions"]:
            if entry["id"] == ver:
                downloadMappings(ver, ver, entry["url"])
                break

        print("Version not found in Mojang version manifest")
    else:
        # Start check task
        check()
