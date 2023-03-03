from subprocess import Popen, PIPE
import os

from lib import args


class Filter:
    results: dict[str, list[str]]

    def __init__(self, name: str, filesToDiff: list[str], lookForDiff: list[str]):
        """
        Creates a filter with the given files and string matches.
        All files but .java files need their file endings specified and have dir separators instead of dots.

        :param name: name of the filter
        :param filesToDiff: qualified file names to always include the full diff of
        :param lookForDiff: string contents to match blobs for
        """
        self.name = name
        self.filesToDiff = filesToDiff
        self.lookForDiff = lookForDiff
        self.results = {}


bufMethods: list[str] = [
    "readWithCodec", "writeWithCodec", "readJsonWithCodec", "writeJsonWithCodec", "writeId", "readById",
    "readCollection", "writeCollection", "readList", "readIntIdList", "writeIntIdList", "readMap", "writeMap",
    "readWithCount", "writeEnumSet", "readEnumSet", "writeOptional", "readOptional", "readNullable",
    "writeNullable", "writeEither", "readEither", "readByteArray", "writeByteArray", "writeVarIntArray",
    "readVarIntArray", "writeLongArray", "readLongArray", "readBlockPos", "writeBlockPos", "readChunkPos",
    "writeChunkPos", "readSectionPos", "writeSectionPos", "readGlobalPos", "writeGlobalPos", "readVector3f",
    "writeVector3f", "readQuaternion", "writeQuaternion", "readComponent", "writeComponent", "readEnum",
    "writeEnum", "readVarInt", "readVarLong", "writeUUID", "readUUID", "writeVarInt", "writeVarLong",
    "writeNbt", "readNbt", "readAnySizeNbt", "writeItem", "readItem", "readUtf", "writeUtf",
    "readResourceLocation", "writeResourceLocation", "readResourceKey", "writeResourceKey", "readDate",
    "writeDate", "readInstant", "writeInstant", "readPublicKey", "writePublicKey", "readBlockHitResult",
    "writeBlockHitResult", "readBitSet", "writeBitSet", "readFixedBitSet", "writeFixedBitSet",
    "readGameProfile", "writeGameProfile", "readGameProfileProperties", "writeGameProfileProperties",
    "readProperty", "writeProperty", "readBoolean", "readByte",
    "readUnsignedByte", "readShort", "readShortLE", "readUnsignedShort", "readUnsignedShortLE", "readMedium",
    "readMediumLE", "readUnsignedMedium", "readUnsignedMediumLE", "readInt", "readIntLE", "readUnsignedInt",
    "readUnsignedIntLE", "readLong", "readLongLE", "readChar", "readFloat", "readDouble", "readBytes",
    "readSlice", "readRetainedSlice", "readCharSequence", "writeBoolean", "writeByte", "writeShort",
    "writeShortLE", "writeMedium", "writeMediumLE", "writeInt", "writeIntLE", "writeLong", "writeLongLE",
    "writeChar", "writeFloat", "writeDouble", "writeBytes", "writeZero", "writeCharSequence"
]
for i in range(len(bufMethods)):
    bufMethods[i] = "." + bufMethods[i] + "("

filters: list[Filter] = [
    Filter("Packets", [], bufMethods),
    Filter("Entity type", ["net.minecraft.world.entity.EntityType"], []),
    Filter("Entity data (for metadata)", ["net.minecraft.network.syncher.SynchedEntityData"], ["EntityDataAccessor<"]),
    Filter("Entity pose (for metadata)", ["net.minecraft.world.entity.Pose"], []),
    Filter("Argument types (serializers)", ["net.minecraft.commands.synchronization.ArgumentTypeInfos"], []),
    Filter("Recipe types (serializers)", ["net.minecraft.world.item.crafting.RecipeSerializer"], []),
    Filter("Particle types (serializers)", ["net.minecraft.core.particles.ParticleTypes"], []),
    Filter("Inventory types", ["net.minecraft.world.inventory.MenuType"], []),
    Filter("Stat types", ["net.minecraft.stats.Stats"], []),
    Filter("Map colors", ["net.minecraft.world.level.material.MaterialColor"], []),
    Filter("Biomes (for backwards mappings)", ["net.minecraft.world.level.biome.Biomes"], []),
    Filter("RegistrySynchronization (NETWORKABLE_REGISTRIES for registry data)",
           ["net.minecraft.core.RegistrySynchronization"], []),
    Filter("Registry data fields", [],
           ["Codec<DimensionType> DIRECT_CODEC =", "MapCodec<DimensionType.MonsterSettings> CODEC =",
            "Codec<Biome> NETWORK_CODEC = ", "Codec<BiomeSpecialEffects> CODEC =",
            "MapCodec<Biome.ClimateSettings> CODEC =", "MapCodec<MobSpawnSettings> CODEC =",
            "Codec<TrimMaterial> DIRECT_CODEC =", "Codec<TrimPattern> DIRECT_CODEC =",
            "Codec<DamageType> CODEC =",
            "Codec<ChatType> CODEC ="]),
    Filter("FriendlyByteBuf (for new/renamed methods to filter)", ["net.minecraft.network.FriendlyByteBuf"], []),
]

# Output argument to dump the output into
toFile: str | None = None
if args.hasArg("output"):
    toFile = args.getArg("output")

currentDir: str = os.getcwd()
os.chdir(os.path.expanduser("~\\IdeaProjects\\MCSources\\"))  # HMMMMMMMMMMM


def hasContainsMatch(blob: str, f: Filter) -> bool:
    """
    Returns whether the given blob contains one of the filter texts.

    :param blob: diff blob
    :param f: filter to check content matches for
    :return: whether the given blob contains one of the filter texts
    """
    for s in f.lookForDiff:
        if s in blob:
            return True
    return False


def processHunk(file: str, hunk: str, additionBlob: str):
    if file is None or hunk is None:
        return

    for f in filters:
        if file in f.filesToDiff or hasContainsMatch(additionBlob, f):
            if file not in f.results:
                f.results[file] = [hunk]
            elif hunk not in f.results[file]:
                f.results[file].append(hunk)


def anyDiffersInChat():
    pp: Popen[bytes] = Popen("git show", stdout=PIPE, stderr=PIPE)
    stdout, stderr = pp.communicate()
    diffLines: list[str] = stdout.decode("utf-8").splitlines()

    currentHunk = None
    currentHunkChanges = None
    currentFile = None

    # todo Check if this works on created/deleted files
    for line in diffLines:
        if line.startswith("@@ "):
            # Beginning of a hunk
            processHunk(currentFile, currentHunk, currentHunkChanges)

            currentHunk = line + "\n"
            currentHunkChanges = ""
            continue

        if line.startswith("diff --git ") or line.startswith("+++ b/") or line.startswith("index "):
            continue

        if line.startswith("--- a/"):
            # Beginning of the diff of another file
            processHunk(currentFile, currentHunk, currentHunkChanges)

            currentFile = line[len("--- a/"):].replace("src/main/java/", "")
            if currentFile.endswith(".java"):
                currentFile = currentFile[:-len(".java")].replace("/", ".")

            currentHunk = None
            currentHunkChanges = None
            continue

        if currentHunk is None:
            continue

        # Add to current hunk/hunk changes
        currentHunk += line + "\n"
        if line.startswith("+") or line.startswith("-"):
            currentHunkChanges += line + "\n"


def printMatches(writeToPath: str | None = None):
    output = ""
    for f in filters:
        if len(f.results) == 0:
            continue

        output += "------------------------------------------------\n"
        output += "MATCHED FILTER: " + f.name + "\n"
        for key in f.results:
            output += key + "\n"
            for blob in f.results[key]:
                output += blob + "\n"
            output += "\n"

    if writeToPath is not None:
        os.chdir(currentDir)
        parent = os.path.dirname(writeToPath)
        if len(parent) != 0 and not os.path.exists(parent):
            os.makedirs(parent)

        with open(writeToPath, 'w') as file:
            file.write(output)
            file.close()
        print("Dumped to file " + writeToPath)
    else:
        print(output)


anyDiffersInChat()
printMatches(toFile)
