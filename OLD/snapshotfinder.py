import urllib.request
import time
import subprocess

counter = 0
version = input("Version?\n")
while True:
    try:
        print("#" + str(counter), flush=True)
        page = urllib.request.urlopen("https://www.minecraft.net/en-us/article/minecraft-snapshot-" + version)
        print("FOUND AFTER", counter * 5, "SECONDS!", flush=True)
        subprocess.call(["py", "snapshotdownloader.py", version])
        break
    except:
        counter += 1
        time.sleep(5)
