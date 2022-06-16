import time
import six.moves.urllib.request
import json
import wget
import subprocess
import os
import shutil
from lib import zips
from lib import args


def loadJson(url):
    with six.moves.urllib.request.urlopen(url) as stream:
        return json.load(stream)


def delete(file):
    try:
        os.remove(file)
    except:
        pass


def saveToFile(release, snapshot):
    versionsFile = open("versions.txt", "w")
    versionsFile.write(release + "\n")
    versionsFile.write(snapshot)
    versionsFile.close()


def processMappings(jsonObject, oldVersion, version):
    clientUrl = jsonObject["downloads"]["client"]["url"]
    serverUrl = jsonObject["downloads"]["server"]["url"]

    if not os.path.isdir("versions"):
        os.mkdir("versions")

    # Client download
    clientFile = "versions/client-" + version + ".jar"
    if os.path.isfile(clientFile):
        print("Client file already present!")
    else:
        print("=== Downloading client from " + clientUrl + "...", flush=True)
        wget.download(clientUrl, clientFile)

    # Server download
    serverFile = "versions/server-" + version + ".jar"
    if os.path.isfile(serverFile):
        print("Server file already present!")
    else:
        print("\n=== Downloading server...", flush=True)
        wget.download(serverUrl, serverFile)

    # Via mapping
    if os.path.isfile("mappings/mapping-" + version + ".json"):
        print("Via mapping file already present!")
    else:
        print("\n=== Starting server mapping generator...\n", flush=True)
        subprocess.call(["java", "-jar", "MappingsGenerator-1.0.jar", "versions/server-" + version + ".jar", version])
        shutil.rmtree('logs')

    # Burger
    vitrineFile = "Burger\\vitrine\\" + oldVersion + "_" + version + ".html"
    if oldVersion == version:
        # Only dump the one version
        if not os.path.isfile("Burger\\out\\" + version + ".json"):
            os.system(".\\burger.sh " + version)
    elif os.path.isfile(vitrineFile):
        print("Burger/Vitrine file already present!")
    else:
        print("\n=== Generating Burger mapping diff...\n", flush=True)
        os.system(".\\burger.sh " + oldVersion + " " + version)
        os.system(".\\" + vitrineFile)

    # Minimize client/server jar
    if not args.hasArg("noMinimize", 'm'):
        print("\nMinimizing client/server jar file...", flush=True)
        zips.delete_from_zip_file(clientFile, "^(assets/realms|assets/minecraft/textures|assets/minecraft/models|assets/minecraft/blockstates|assets/minecraft/shaders)\/")
        zips.delete_from_zip_file(serverFile,
                                  "^(data|assets|META-INF|com/google|io|it|javax|org|joptsimple|oshi|com/sun)\/")

    # Sources export
    if args.hasArg("generateSourcesButBetter", 'v'):
        print("\n=== Decompiling sources with VanillaGradle...\n", flush=True)
        os.system("py sources.py --decompile --push --ver " + version)

    if args.hasArg("generateSources", 's'):
        print("\n=== Generating sources with Enigma...\n", flush=True)
        clientMappingsUrl = jsonObject["downloads"]["client_mappings"]["url"]
        serverMappingsUrl = jsonObject["downloads"]["server_mappings"]["url"]
        if not os.path.isdir("sources"):
            os.mkdir("sources")

        print("\nGenerating client sources...\n", flush=True)
        wget.download(clientMappingsUrl, "sources/client-" + version + ".txt")
        os.system(".\\generate-sources.sh client " + version)

        # print("\nGenerating server sources...\n", flush=True)
        # wget.download(serverMappingsUrl, "sources/server-" + version + ".txt")
        # os.system(".\\generate-sources.sh server " + version)

    print("\nFinished", version, "processing!", flush=True)


def downloadMappings(oldVersion, version, url):
    if oldVersion == "":
        oldVersion = version

    jsonObject = loadJson(url)

    with open("versions/" + version + ".json", 'w') as file:
        json.dump(jsonObject, file)

    processMappings(jsonObject, oldVersion, version)


def check():
    try:
        versionsFile = open("versions.txt", "r")
        oldVersions = versionsFile.read().split("\n")
        versionsFile.close()
        oldRelease = oldVersions[0]
        oldSnapshot = oldVersions[1]
    except IOError:
        oldRelease = ""
        oldSnapshot = ""

    attempt = 0
    while True:
        attempt += 1
        print("Checking #" + str(attempt), flush=True)

        jsonObject = loadJson("https://piston-meta.mojang.com/mc/game/version_manifest_v2.json")

        latest = jsonObject["latest"]
        latestRelease = latest["release"]
        latestSnapshot = latest["snapshot"]

        if oldRelease != latestRelease:
            print("A new release has been published:", latestRelease, flush=True)
            old = oldRelease
            new = latestRelease
            oldRelease = latestRelease

            saveToFile(latestRelease, oldSnapshot)
        elif oldSnapshot != latestSnapshot:
            print("A new snapshot has been published:", latestSnapshot, flush=True)
            old = oldSnapshot
            new = latestSnapshot
            oldSnapshot = latestSnapshot

            saveToFile(oldRelease, latestSnapshot)
        else:
            time.sleep(20)
            continue

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
    ver = args.getArg("ver")
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
    else:
        # Start check task
        check()
