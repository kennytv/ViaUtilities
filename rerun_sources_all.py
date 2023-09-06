from version_checker import *
from datetime import datetime


def has_mappings(version: str):
    if version.find(' ') != -1:
        return False  # Bad

    # Snapshots since 19w36a and releases from 1.14.4 onwards have obfuscation mappings
    if version.find('w') != -1:
        if len(version) > 6:
            return False  # Bad

        year, week = version.split('w')
        return int(year) == 19 and int(week[:2]) >= 36 or int(year) > 19

    components = version.split('-')[0].split('.')
    try:
        major = int(components[1])
        minor = int(components[2]) if len(components) > 2 else 0
    except:
        # Alpha/classic releases or probably April Fools snapshots
        return False

    return major == 14 and minor == 4 and version.find('-') == -1 or major > 14


# Get all main-line versions with mappings and sort them by release time
versions = []
include_snapshots = True
start_at = None  # Manual override, set to None to actually run all

for entry in get_json_from_url(MANIFEST_URL)["versions"]:
    version_string: str = entry["id"]
    version_type: str = entry["type"]
    if has_mappings(version_string) and (include_snapshots and version_type == "snapshot" or version_type == "release"):
        time = datetime.fromisoformat(entry["releaseTime"]).timestamp()
        versions.append({"version": version_string, "time": time, "url": entry["url"]})

versions.sort(key=lambda obj: obj["time"])

# Decompile deobfuscate them all
go = start_at is None
for version in versions:
    version_string = version["version"]
    if not go:
        if version_string != start_at:
            continue
        go = True

    print("=========== " + version_string)
    json_object = get_json_from_url(version["url"])
    with open("versions/" + version_string + ".json", 'w') as version_file:
        json.dump(json_object, version_file)

    os.system("python sources.py --decompile --push --ver " + version_string)
