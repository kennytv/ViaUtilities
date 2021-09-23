import glob
import subprocess
import zipfile
import shutil
import os
from lib import args

decompile = args.hasArg("decompile", 'd')
version = args.getArg("ver")
push = args.hasArg("push", 'p')
# Hmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm
sourcesDir = "C:\\Users\\Nassim\\IdeaProjects\\MCSources\\"
sourcesJavaDir = sourcesDir + "src\\main\\java\\"

shutil.copyfile("versions\\" + version + ".json", sourcesDir + "manual.json")

os.chdir(sourcesDir)

if decompile:
    print("Decompiling...", flush=True)
    os.system("gradlew decompile")

if os.path.isdir(sourcesJavaDir):
    print("Deleting old sources...", flush=True)
    shutil.rmtree(sourcesJavaDir, ignore_errors=False, onerror=None)

print("Unzipping and moving sources...")
os.mkdir(sourcesJavaDir)
for jar in glob.glob(
        f"C:\\Users\\Nassim\\.gradle\\caches\\VanillaGradle\\v1\\jars\\net\\minecraft\\joined\\{version}\\joined-{version}-sources.jar"):
    with zipfile.ZipFile(jar) as z:
        z.extractall(path=sourcesJavaDir)
    break

if push:
    os.chdir(sourcesDir)
    print("Committing and pushing...", flush=True)
    os.system("git add . && git commit --no-signoff -am \"" + version + "\" && git push")

print("Done.")
