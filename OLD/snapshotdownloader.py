import urllib.request
import wget
import subprocess
import os
import sys

version = ""
if len(sys.argv) == 2:  # 1. is file name in console
    version = sys.argv[1]
else:
    version = input("Version?\n")

try:
    os.remove("server.jar")
except:
    print()

page = urllib.request.urlopen("https://www.minecraft.net/en-us/article/minecraft-snapshot-" + version)
content = str(page.read())
link = content.split("\">Minecraft server jar")[0].split("https://launcher.mojang.com/v1/objects/")[1]
print("=== Downloading...", flush=True)
wget.download("https://launcher.mojang.com/v1/objects/" + link, "server.jar")

print("\n=== Starting mapping process...\n", flush=True)
subprocess.call(["java", "-jar", "MappingsGenerator-1.0.jar", version])
print("\nDone!")
