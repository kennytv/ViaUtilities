import glob
import zipfile
import shutil
import os
import platform
from os.path import expanduser
from lib import args

fromCache: bool = args.hasArg("fromCache", 'c')
decompile: bool = args.hasArg("decompile", 'd')
version: str = args.getArg("ver")
push: bool = args.hasArg("push", 'p')
# Hmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm
sourcesDir: str = expanduser(os.path.join("~", "IdeaProjects", "MCSources"))
sourcesJavaDir: str = os.path.join(sourcesDir, "src", "main", "java")

if not fromCache:
    shutil.copyfile(os.path.join("versions", version + ".json"), os.path.join(sourcesDir, "version.json"))

os.chdir(sourcesDir)

if decompile:
    print("Decompiling...", flush=True)
    if platform.system() == "Windows":
        os.system("gradlew decompile --stacktrace")
    else:
        os.system("./gradlew decompile --stacktrace")

if os.path.isdir(sourcesJavaDir):
    print("Deleting old sources...", flush=True)
    shutil.rmtree(sourcesJavaDir, ignore_errors=False, onerror=None)

print("Unzipping and moving sources...")
os.mkdir(sourcesJavaDir)

jarPath = expanduser(os.path.join(
    "~", ".gradle", "caches", "VanillaGradle", "v2", "jars", "net", "minecraft", "joined", version,
    f"joined-{version}-sources.jar"
))
for jar in glob.glob(jarPath):
    with zipfile.ZipFile(jar) as z:
        # z.extractall(path=sourcesJavaDir)
        for file_info in z.infolist():
            # Extract files except those in 'assets' and 'data' directories
            if not file_info.filename.startswith(('assets/', 'data/')):
                z.extract(file_info, path=sourcesJavaDir)
    break

with open(os.path.join(sourcesDir, "last.txt"), 'w') as file:
    file.write(version)

if push:
    os.chdir(sourcesDir)
    print("Committing and pushing...", flush=True)
    os.system("git pull && git add . && git commit --no-signoff -am \"" + version + "\" && git push")

print("Done.")
