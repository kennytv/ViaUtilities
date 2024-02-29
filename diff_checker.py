from subprocess import Popen, PIPE
import os

from lib import args


class Filter:
    results: dict[str, list[str]]

    def __init__(self, name: str, files_to_diff: list[str], look_for_diff: list[str]):
        """
        Creates a filter with the given files and string matches.
        All files but .java files need their file endings specified and have dir separators instead of dots.

        :param name: name of the filter
        :param files_to_diff: qualified file names to always include the full diff of
        :param look_for_diff: string contents to match blobs for
        """
        self.name = name
        self.filesToDiff = files_to_diff
        self.lookForDiff = look_for_diff
        self.results = {}


# A lot of these aren't valid anymore
buf_methods: list[str] = [
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
    "writeChar", "writeFloat", "writeDouble", "writeBytes", "writeZero", "writeCharSequence",
    'StreamCodec', 'ByteBufCodecs'
]
for i in range(len(buf_methods)):
    buf_methods[i] = "." + buf_methods[i] + "("

filters: list[Filter] = [
    Filter("Packets", [], buf_methods),
    Filter("Entity type", ["net.minecraft.world.entity.EntityType"], []),
    Filter("Data components", ["net.minecraft.core.component.DataComponents"], []),
    Filter("Entity data (for metadata)", ["net.minecraft.network.syncher.SynchedEntityData"], ["EntityDataAccessor<"]),
    Filter("Entity pose (for metadata)", ["net.minecraft.world.entity.Pose"], []),
    Filter("Argument types (serializers)", ["net.minecraft.commands.synchronization.ArgumentTypeInfos"], []),
    Filter("Recipe types (serializers)", ["net.minecraft.world.item.crafting.RecipeSerializer"], []),
    Filter("Particle types (serializers)", ["net.minecraft.core.particles.ParticleTypes"], []),
    Filter("Inventory types", ["net.minecraft.world.inventory.MenuType"], []),
    Filter("Stat types", ["net.minecraft.stats.Stats"], []),
    Filter("Map colors",
           ["net.minecraft.world.level.material.MaterialColor", "net.minecraft.world.level.material.MapColor"], []),
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
to_file: str | None = None
if args.hasArg("output"):
    to_file = args.getArg("output")

current_dir: str = os.getcwd()
os.chdir(os.path.expanduser(os.path.join("~", "IdeaProjects", "MCSources")))  # HMMMMMMMMMMM

def has_contains_match(blob: str, f: Filter) -> bool:
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


def process_hunk(file: str, hunk: str, addition_blob: str):
    if file is None or hunk is None:
        return

    for f in filters:
        if file in f.filesToDiff or has_contains_match(addition_blob, f):
            if file not in f.results:
                f.results[file] = [hunk]
            elif hunk not in f.results[file]:
                f.results[file].append(hunk)


def any_differs_in_chat():
    pp: Popen[bytes] = Popen(["git", "show"], stdout=PIPE, stderr=PIPE)
    stdout, stderr = pp.communicate()
    diff_lines: list[str] = stdout.decode("utf-8").splitlines()

    current_hunk = None
    current_hunk_changes = None
    current_file = None

    # todo Check if this works on created/deleted files
    for line in diff_lines:
        if line.startswith("@@ "):
            # Beginning of a hunk
            process_hunk(current_file, current_hunk, current_hunk_changes)

            current_hunk = line + "\n"
            current_hunk_changes = ""
            continue

        if line.startswith("diff --git ") or line.startswith("+++ b/") or line.startswith("index "):
            continue

        if line.startswith("--- a/"):
            # Beginning of the diff of another file
            process_hunk(current_file, current_hunk, current_hunk_changes)

            current_file = line[len("--- a/"):].replace("src/main/java/", "")
            if current_file.endswith(".java"):
                current_file = current_file[:-len(".java")].replace("/", ".")

            current_hunk = None
            current_hunk_changes = None
            continue

        if current_hunk is None:
            continue

        # Add to current hunk/hunk changes
        current_hunk += line + "\n"
        if line.startswith("+") or line.startswith("-"):
            current_hunk_changes += line + "\n"


def print_matches(write_to_path: str | None = None):
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

    if write_to_path is not None:
        os.chdir(current_dir)
        parent = os.path.dirname(write_to_path)
        if len(parent) != 0 and not os.path.exists(parent):
            os.makedirs(parent)

        with open(write_to_path, 'w') as file:
            file.write(output)
            file.close()
        print("Dumped to file " + write_to_path)
    else:
        print(output)


any_differs_in_chat()
print_matches(to_file)
