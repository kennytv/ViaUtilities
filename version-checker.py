import time
import six.moves.urllib.request
import json
import wget
import subprocess
import os

burgerDir = "C:\\Users\\Nassim\\Desktop\\Burger\\"


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

    clientFile = burgerDir + "versions\\" + version + ".jar"
    if os.path.isfile(clientFile):
        print("Client file already present!", flush=True)
    else:
        print("=== Downloading client...", flush=True)
        wget.download(clientUrl, clientFile)

    print("\n=== Downloading server...", flush=True)
    wget.download(serverUrl, "server.jar")

    print("\n=== Starting server mapping generator...\n", flush=True)
    subprocess.call(["java", "-jar", "MappingsGenerator-1.0.jar", version])

    print("\n=== Generating Burger mapping diff...\n", flush=True)
    os.system("cd " + burgerDir +
              " && .\\update.sh " + oldVersion + " " + version +
              " && .\\vitrine\\" + oldVersion + "_" + version + ".html")

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

    while True:
        print("Checking.", flush=True)

        # raw =
        # jsonObject = json.load(raw)
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

        time.sleep(20)


delete("server.jar")
check()
