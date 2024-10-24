import shutil
import os
import subprocess
import platform
from os.path import expanduser
from lib import args

version: str = args.getArg("ver")
push: bool = args.hasArg("push", 'p')
# Hmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm
sourcesDir: str = expanduser(os.path.join("~", "IdeaProjects", "MinecraftSauce"))
sourcesJavaDir: str = os.path.join(sourcesDir, "versionProject", "src", "main", "java")

os.chdir(sourcesDir)

if os.path.isdir(sourcesJavaDir):
    print("Deleting old sources...", flush=True)
    shutil.rmtree(sourcesJavaDir, ignore_errors=False, onerror=None)

env = dict(os.environ)
env['CI'] = 'false'

print("Decompiling...", flush=True)
if platform.system() == "Windows":
    os.system(f"gradlew :versionProject:applyPatches -PmcVer={version} --stacktrace")
else:
    os.system(f"./gradlew :versionProject:applyPatches -PmcVer={version} --stacktrace")

try:
    shutil.rmtree("versionProject/src/main/java/.git")
except PermissionError as o:
    print("Permission error, force deleting dir", flush=True)
    subprocess.run(['rm', '-rf', 'versionProject/src/main/java/.git'], check=True)

if push:
    os.chdir(sourcesDir)
    print("Committing and pushing...", flush=True)
    os.system("git pull && git add . && git commit --no-signoff -am \"" + version + "\" && git push")

print("Done.")
