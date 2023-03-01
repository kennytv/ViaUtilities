from subprocess import Popen, PIPE
import os
from lib import args


class Filter:

    def __init__(self, name, filesToDiff, lookForDiff):
        self.name = name
        self.filesToDiff = filesToDiff
        self.lookForDiff = lookForDiff
        self.results = {}


bufMethods = [
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

filters = [
    Filter("Packets", [], bufMethods),
    Filter("Entity type", ["net.minecraft.world.entity.EntityType"], []),
    Filter("Entity data (for metadata)", ["net.minecraft.network.syncher.SynchedEntityData"], ["EntityDataAccessor<"]),
    Filter("Entity pose (for metadata)", ["net.minecraft.world.entity.Pose"], []),
    Filter("Argument types (serializers)", ["net.minecraft.commands.synchronization.ArgumentTypeInfos"], []),
    Filter("Recipe types (serializers)", ["net.minecraft.world.item.crafting.RecipeSerializer"], []),
    Filter("Particle types (serializers)", ["net.minecraft.core.particles.ParticleTypes"], []),
    Filter("Inventory types", ["net.minecraft.world.inventory.MenuType"], []),
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

toFile = None
if args.hasArg("output"):
    toFile = args.getArg("output")

currentDir = os.getcwd()
os.chdir(os.path.expanduser("~\\IdeaProjects\\MCSources\\"))


def hasContainsMatch(blob, lookForDiff):
    for s in lookForDiff:
        if s in blob:
            return True
    return False


def checkBlob(file, blob, additionBlob):
    if file is None or blob is None:
        return

    for filter in filters:
        if file in filter.filesToDiff or hasContainsMatch(additionBlob, filter.lookForDiff):
            if file not in filter.results:
                filter.results[file] = [blob]
            elif blob not in filter.results[file]:
                filter.results[file].append(blob)


def anyDiffersInChat():
    pp = Popen("git show", stdout=PIPE, stderr=PIPE)
    stdout, stderr = pp.communicate()
    files_changed_list = stdout.decode("utf-8").splitlines()
    currentBlob = None
    currentAdditionBlob = None
    currentFile = None
    # todo Check if this works on created/deleted files
    for line in files_changed_list:
        if line.startswith("@@ "):
            checkBlob(currentFile, currentBlob, currentAdditionBlob)

            currentBlob = line + "\n"
            currentAdditionBlob = ""
            continue

        if line.startswith("diff --git ") or line.startswith("+++ b/") or line.startswith("index "):
            continue

        if line.startswith("--- a/"):
            checkBlob(currentFile, currentBlob, currentAdditionBlob)

            currentFile = line[len("--- a/"):].replace("src/main/java/", "")
            if currentFile.endswith(".java"):
                currentFile = currentFile[:-len(".java")].replace("/", ".")

            currentBlob = None
            currentAdditionBlob = None
            continue

        if currentBlob is not None:
            currentBlob += line + "\n"
            if line.startswith("+") or line.startswith("-"):
                currentAdditionBlob += line + "\n"


def printMatches(writeToPath=None):
    s = ""
    for f in filters:
        if len(f.results) == 0:
            continue

        s += "------------------------------------------------\n"
        s += "MATCHED FILTER: " + f.name + "\n"
        for key in f.results:
            s += key + "\n"
            for blob in f.results[key]:
                s += blob + "\n"
            s += "\n"

    if writeToPath is not None:
        os.chdir(currentDir)
        parent = os.path.dirname(writeToPath)
        if len(parent) != 0 and not os.path.exists(parent):
            os.makedirs(parent)

        with open(writeToPath, 'w') as file:
            file.write(s)
            file.close()
        print("Dumped to file " + writeToPath)
    else:
        print(s)


anyDiffersInChat()
printMatches(toFile)
