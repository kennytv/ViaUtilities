import glob
import zipfile
import shutil
import os
from os.path import expanduser
from lib import args

fromCache: bool = args.hasArg("fromCache", 'c')
decompile: bool = args.hasArg("decompile", 'd')
version: str = args.getArg("ver")
push: bool = args.hasArg("push", 'p')
# Hmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm
sourcesDir: str = expanduser("~\\IdeaProjects\\MCSources\\")
sourcesJavaDir: str = sourcesDir + "src\\main\\java\\"

if not fromCache:
    shutil.copyfile("versions\\" + version + ".json", sourcesDir + "version.json")

os.chdir(sourcesDir)

if decompile:
    print("Decompiling...", flush=True)
    os.system("gradlew decompile")

if os.path.isdir(sourcesJavaDir):
    print("Deleting old sources...", flush=True)
    shutil.rmtree(sourcesJavaDir, ignore_errors=False, onerror=None)

print("Unzipping and moving sources...")
os.mkdir(sourcesJavaDir)
for jar in glob.glob(expanduser(
        f"~\\.gradle\\caches\\VanillaGradle\\v2\\jars\\net\\minecraft\\joined\\{version}\\joined-{version}-sources.jar")):
    with zipfile.ZipFile(jar) as z:
        z.extractall(path=sourcesJavaDir)
    break

with open(sourcesDir + "\\last.txt", 'w') as file:
    file.write(version)

if push:
    os.chdir(sourcesDir)
    print("Committing and pushing...", flush=True)
    os.system("git pull && git add . && git commit --no-signoff -am \"" + version + "\" && git push")

print("Done.")
