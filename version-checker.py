import time
import six.moves.urllib.request
import json
import wget
import subprocess
import os
import sys

enigmaPath = "enigma-cli.jar"


def hasArg(arg):
    for argv in sys.argv:
        if argv == arg:
            return True
    return False


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


def downloadMappings(oldVersion, version, url):
    if oldVersion == "":
        oldVersion = version

    jsonObject = loadJson(url)
    clientUrl = jsonObject["downloads"]["client"]["url"]
    serverUrl = jsonObject["downloads"]["server"]["url"]

    clientFile = "versions/client-" + version + ".jar"
    if os.path.isfile(clientFile):
        print("=== Downloading client...", flush=True)
        wget.download(clientUrl, clientFile)
    else:
        print("Client file already found!")

    serverFile = "versions/server-" + version + ".jar"
    if os.path.isfile(clientFile):
        print("\n=== Downloading server...", flush=True)
        wget.download(serverUrl, serverFile)
    else:
        print("Server file already found!")

    print("\n=== Starting server mapping generator...\n", flush=True)
    subprocess.call(["java", "-jar", "MappingsGenerator-1.0.jar", "versions/server-" + version + ".jar", version])

    print("\n=== Generating Burger mapping diff...\n", flush=True)
    os.system(".\\update.sh " + oldVersion + " " + version +
              " && .\\Burger\\vitrine\\" + oldVersion + "_" + version + ".html")

    if hasArg("--generateSources"):
        print("\n=== Generating sources with Enigma...\n", flush=True)
        clientMappingsUrl = jsonObject["downloads"]["client_mappings"]["url"]
        serverMappingsUrl = jsonObject["downloads"]["server_mappings"]["url"]
        proguardMappingsPath = "sources/" + version + ".txt"

        # Client sources
        wget.download(clientMappingsUrl, proguardMappingsPath)
        os.system(".\\generate-sources.sh " + version + " " + enigmaPath)
        delete(proguardMappingsPath)

        # Server sources
        wget.download(serverMappingsUrl, proguardMappingsPath)
        os.system(".\\generate-sources.sh " + version + " " + enigmaPath)
        delete(proguardMappingsPath)

    print("\nFinished", version, "processing!", flush=True)


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

        jsonObject = loadJson("https://launchermeta.mojang.com/mc/game/version_manifest.json")

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


check()
