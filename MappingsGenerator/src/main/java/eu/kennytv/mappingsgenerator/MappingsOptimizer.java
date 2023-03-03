/*
 * This file is part of ViaUtilities - https://github.com/kennytv/ViaUtilities
 * Copyright (C) 2023 Nassim Jahnke
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */
package eu.kennytv.mappingsgenerator;

import com.github.steveice10.opennbt.NBTIO;
import com.github.steveice10.opennbt.tag.builtin.ByteTag;
import com.github.steveice10.opennbt.tag.builtin.CompoundTag;
import com.github.steveice10.opennbt.tag.builtin.IntArrayTag;
import com.github.steveice10.opennbt.tag.builtin.IntTag;
import com.github.steveice10.opennbt.tag.builtin.ListTag;
import com.github.steveice10.opennbt.tag.builtin.StringTag;
import com.github.steveice10.opennbt.tag.builtin.Tag;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import eu.kennytv.mappingsgenerator.util.JsonConverter;
import it.unimi.dsi.fastutil.ints.Int2IntMap;
import it.unimi.dsi.fastutil.objects.Object2IntMap;
import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.jetbrains.annotations.Nullable;

public final class MappingsOptimizer {

    public static final File OUTPUT_DIR = new File("output");
    public static final File MAPPINGS_DIR = new File("mappings");
    private static final Set<String> STANDARD_FIELDS = Set.of("blockstates", "blocks", "items", "sounds", "blockentities", "enchantments", "paintings", "entities", "particles", "argumenttypes", "statistics", "tags");
    private static final int VERSION = 1;
    private static final byte DIRECT_ID = 0;
    private static final byte SHIFTS_ID = 1;
    private static final byte CHANGES_ID = 2;
    private static final byte IDENTITY_ID = 3;
    private static final String DILL_FILE_FORMAT = "mappingdiff-%sto%s.json";
    private static final String MAPPING_FILE_FORMAT = "mapping-%s.json";
    private static final String OUTPUT_FILE_FORMAT = "mappings-%sto%s.nbt";
    private static final String OUTPUT_IDENTIFIERS_FILE_FORMAT = "identifiers-%s.nbt";
    private static final Set<String> SAVED_IDENTIFIER_FILES = new HashSet<>();
    private static final boolean RUN_ALL = true;

    public static void main(final String[] args) throws IOException {
        MAPPINGS_DIR.mkdirs();
        OUTPUT_DIR.mkdirs();

        if (RUN_ALL) {
            runAll();
            return;
        }

        final String from = args.length == 2 ? args[0] : "1.16.2";
        final String to = args.length == 2 ? args[1] : "1.17";
        optimizeAndSaveAsNBT(from, to);
    }

    /**
     * Optimizes mapping files as nbt files with only the necessary data (int to int mappings in form of int arrays).
     *
     * @param from version to map from
     * @param to   version to map to
     */
    private static void optimizeAndSaveAsNBT(final String from, final String to) throws IOException {
        final JsonObject unmappedObject = MappingsLoader.load(MAPPING_FILE_FORMAT.formatted(from));
        final JsonObject mappedObject = MappingsLoader.load(MAPPING_FILE_FORMAT.formatted(to));
        final JsonObject diffObject = MappingsLoader.load(DILL_FILE_FORMAT.formatted(from, to));
        if (unmappedObject == null) {
            throw new IllegalArgumentException("Mapping file for version " + from + " does not exist");
        }
        if (mappedObject == null) {
            throw new IllegalArgumentException("Mapping file for version " + to + " does not exist");
        }

        final CompoundTag tag = new CompoundTag();
        tag.put("version", new IntTag(VERSION));

        handleUnknownFields(tag, unmappedObject);

        mappings(tag, unmappedObject, mappedObject, diffObject, true, true, "blockstates");
        mappings(tag, unmappedObject, mappedObject, diffObject, true, false, "blocks");
        mappings(tag, unmappedObject, mappedObject, diffObject, true, false, "items");
        mappings(tag, unmappedObject, mappedObject, diffObject, true, false, "sounds");
        mappings(tag, unmappedObject, mappedObject, diffObject, true, false, "blockentities");
        mappings(tag, unmappedObject, mappedObject, diffObject, true, false, "enchantments");
        mappings(tag, unmappedObject, mappedObject, diffObject, true, false, "paintings");
        mappings(tag, unmappedObject, mappedObject, diffObject, true, false, "entities");
        mappings(tag, unmappedObject, mappedObject, diffObject, true, false, "particles");
        mappings(tag, unmappedObject, mappedObject, diffObject, true, false, "argumenttypes");
        mappings(tag, unmappedObject, mappedObject, diffObject, true, false, "statistics");
        if (diffObject != null && diffObject.has("tags")) {
            final CompoundTag tagsTag = new CompoundTag();
            tags(tagsTag, mappedObject, diffObject);
            tag.put("tags", tagsTag);
        }
        NBTIO.writeFile(tag, new File(OUTPUT_DIR, OUTPUT_FILE_FORMAT.formatted(from, to)), false, false);

        // Save full identifiers to a separate file per version
        saveIdentifierFiles(from, unmappedObject);
        saveIdentifierFiles(to, mappedObject);
    }

    private static void saveIdentifierFiles(final String version, final JsonObject object) throws IOException {
        final CompoundTag identifiers = new CompoundTag();
        storeIdentifiers(identifiers, object, "entities");
        storeIdentifiers(identifiers, object, "particles");
        storeIdentifiers(identifiers, object, "argumenttypes");
        if (SAVED_IDENTIFIER_FILES.add(version)) {
            NBTIO.writeFile(identifiers, new File(OUTPUT_DIR, OUTPUT_IDENTIFIERS_FILE_FORMAT.formatted(version)), false, false);
        }
    }

    private static void optimizeAndSaveOhSoSpecial1_12AsNBT() throws IOException {
        final JsonObject unmappedObject = MappingsLoader.load("mapping-1.12.json");
        final JsonObject mappedObject = MappingsLoader.load("mapping-1.13.json");

        final CompoundTag tag = new CompoundTag();
        tag.put("v", new IntTag(VERSION));
        handleUnknownFields(tag, unmappedObject);

        cursedMappings(tag, unmappedObject, mappedObject, "blocks", "blockstates", 4084);
        cursedMappings(tag, unmappedObject, mappedObject, "items", "items", unmappedObject.getAsJsonObject("items").size());
        cursedMappings(tag, unmappedObject, mappedObject, "legacy_enchantments", "enchantments", 72);
        mappings(tag, unmappedObject, mappedObject, null, true, false, "sounds");

        NBTIO.writeFile(tag, new File(OUTPUT_DIR, "mappings-1.12to1.13.nbt"), false, false);
    }

    private static void handleUnknownFields(final CompoundTag tag, final JsonObject unmappedObject) {
        for (final String key : unmappedObject.keySet()) {
            if (STANDARD_FIELDS.contains(key)) {
                continue;
            }

            System.out.println("========== NON-STANDARD FIELD: " + key + " - writing it to the file without changes ==========");
            final Tag asTag = JsonConverter.toTag(unmappedObject.get(key));
            tag.put(key, asTag);
        }
    }

    /**
     * Runs the optimizer for all mapping files present in the mappings/ directory.
     */
    private static void runAll() throws IOException {
        final List<String> versions = new ArrayList<>();
        for (final File file : MAPPINGS_DIR.listFiles()) {
            final String name = file.getName();
            if (name.startsWith("mapping-")) {
                versions.add(name.substring("mapping-".length(), name.length() - ".json".length()));
            }
        }

        Collections.sort(versions);
        for (int i = 0; i < versions.size() - 1; i++) {
            final String from = versions.get(i);
            final String to = versions.get(i + 1);
            System.out.println("------------------------------");
            System.out.println("Running " + from + " to " + to);
            if (from.equals("1.12") && to.equals("1.13")) {
                optimizeAndSaveOhSoSpecial1_12AsNBT();
                continue;
            }

            optimizeAndSaveAsNBT(from, to);
        }
    }

    /**
     * Reads mappings from the unmapped and mapped objects and writes them to the nbt tag.
     *
     * @param tag                 tag to write to
     * @param unmappedObject      unmapped mappings object
     * @param mappedObject        mapped mappings object
     * @param diffMappings        diff mappings object
     * @param warnOnMissing       whether to warn on missing mappings
     * @param alwaysWriteIdentity whether to always write the identity mapping with size and mapped size, even if the two arrays are equal
     * @param key                 to read from and write to
     */
    private static void mappings(
            final CompoundTag tag,
            final JsonObject unmappedObject,
            final JsonObject mappedObject,
            @Nullable final JsonObject diffMappings,
            final boolean warnOnMissing,
            final boolean alwaysWriteIdentity,
            final String key
    ) {
        if (!unmappedObject.has(key) || !mappedObject.has(key)) {
            return;
        }

        final JsonArray unmappedIdentifiers = unmappedObject.getAsJsonArray(key);
        final JsonArray mappedIdentifiers = mappedObject.getAsJsonArray(key);
        if (unmappedIdentifiers.equals(mappedIdentifiers) && !alwaysWriteIdentity) {
            System.out.println(key + ": Skipped");
            return;
        }

        final JsonObject diffIdentifiers = diffMappings != null ? diffMappings.getAsJsonObject(key) : null;
        final MappingsLoader.MappingsResult result = MappingsLoader.map(unmappedIdentifiers, mappedIdentifiers, diffIdentifiers, warnOnMissing);
        serialize(result, tag, key, alwaysWriteIdentity);
    }

    private static void cursedMappings(
            final CompoundTag tag,
            final JsonObject unmappedObject,
            final JsonObject mappedObject,
            final String cursedKey,
            final String key,
            final int size
    ) {
        final JsonArray mappedArray = mappedObject.getAsJsonArray(key);
        final Int2IntMap map = MappingsLoader.map(
                unmappedObject.getAsJsonObject(cursedKey),
                JsonConverter.toJsonObject(mappedArray),
                null,
                true
        );

        final CompoundTag changedTag = new CompoundTag();
        final int[] unmapped = new int[map.size()];
        final int[] mapped = new int[map.size()];
        int i = 0;
        for (final Int2IntMap.Entry entry : map.int2IntEntrySet()) {
            unmapped[i] = entry.getIntKey();
            mapped[i] = entry.getIntValue();
            i++;
        }

        changedTag.put("id", new ByteTag(CHANGES_ID));
        changedTag.put("nofill", new ByteTag((byte) 1));
        changedTag.put("size", new IntTag(size));
        changedTag.put("mappedSize", new IntTag(mappedArray.size()));
        changedTag.put("at", new IntArrayTag(unmapped));
        changedTag.put("val", new IntArrayTag(mapped));
        tag.put(key, changedTag);
    }

    /**
     * Writes mapped tag ids to the given tag.
     *
     * @param data         tag to write to
     * @param mappedObject mapped mappings object
     * @param diffObject   diff mappings object
     */
    private static void tags(final CompoundTag data, final JsonObject mappedObject, final JsonObject diffObject) {
        final JsonObject tagsObject = diffObject.getAsJsonObject("tags");
        for (final Map.Entry<String, JsonElement> entry : tagsObject.entrySet()) {
            final JsonObject object = entry.getValue().getAsJsonObject();
            final CompoundTag tag = new CompoundTag();
            final String type = entry.getKey();
            data.put(type, tag);

            final String typeKey = switch (type) {
                case "block" -> "blocks";
                case "item" -> "items";
                case "entity_types" -> "entities";
                default -> throw new IllegalArgumentException("Registry type not supported: " + type);
            };
            final JsonArray typeElements = mappedObject.get(typeKey).getAsJsonArray();
            final Object2IntMap<String> typeMap = MappingsLoader.arrayToMap(typeElements);

            for (final Map.Entry<String, JsonElement> tagEntry : object.entrySet()) {
                final JsonArray elements = tagEntry.getValue().getAsJsonArray();
                final int[] tagIds = new int[elements.size()];
                final String tagName = tagEntry.getKey();
                for (int i = 0; i < elements.size(); i++) {
                    final String element = elements.get(i).getAsString();
                    final int mappedId = typeMap.getInt(element.replace("minecraft:", ""));
                    if (mappedId == -1) {
                        System.err.println("Could not find id for " + element);
                        continue;
                    }

                    tagIds[i] = mappedId;
                }

                tag.put(tagName, new IntArrayTag(tagIds));
            }
        }
    }

    /**
     * Stores a list of string identifiers in the given tag.
     *
     * @param tag    tag to write to
     * @param object object to read identifiers from
     * @param key    to read from and write to
     */
    private static void storeIdentifiers(
            final CompoundTag tag,
            final JsonObject object,
            final String key
    ) {
        final JsonArray identifiers = object.getAsJsonArray(key);
        if (identifiers == null) {
            return;
        }

        final ListTag list = new ListTag(StringTag.class);
        for (final JsonElement identifier : identifiers) {
            list.add(new StringTag(identifier.getAsString()));
        }

        tag.put(key, list);
    }

    /**
     * Writes an int to int mappings result to the ntb tag.
     *
     * @param result              result with int to int mappings
     * @param parent              tag to write to
     * @param key                 key to write to
     * @param alwaysWriteIdentity whether to write identity mappings even if there are no changes
     */
    private static void serialize(final MappingsLoader.MappingsResult result, final CompoundTag parent, final String key, boolean alwaysWriteIdentity) {
        final int[] mappings = result.mappings();
        final int numberOfChanges = mappings.length - result.identityMappings();
        final boolean hasChanges = numberOfChanges != 0 || result.emptyMappings() != 0;
        if (!hasChanges && !alwaysWriteIdentity) {
            System.out.println(key + ": Skipped due to no relevant id changes");
            return;
        }

        final CompoundTag tag = new CompoundTag();
        parent.put(key, tag);
        tag.put("mappedSize", new IntTag(result.mappedSize()));

        if (!hasChanges) {
            tag.put("id", new ByteTag(IDENTITY_ID));
            tag.put("size", new IntTag(mappings.length));
            return;
        }

        final int changedFormatSize = approximateChangedFormatSize(result);
        final int shiftFormatSize = approximateShiftFormatSize(result);
        final int plainFormatSize = mappings.length;
        if (changedFormatSize < plainFormatSize && changedFormatSize < shiftFormatSize) {
            // Put two intarrays of only changed ids instead of adding an entry for every single identifier
            System.out.println(key + ": Storing as changed and mapped arrays");
            tag.put("id", new ByteTag(CHANGES_ID));
            tag.put("size", new IntTag(mappings.length));

            final int[] unmapped = new int[numberOfChanges];
            final int[] mapped = new int[numberOfChanges];
            int index = 0;
            for (int i = 0; i < mappings.length; i++) {
                final int mappedId = mappings[i];
                if (mappedId != i) {
                    unmapped[index] = i;
                    mapped[index] = mappedId;
                    index++;
                }
            }

            if (index != numberOfChanges) {
                throw new IllegalStateException("Index " + index + " does not equal number of changes " + numberOfChanges);
            }

            tag.put("at", new IntArrayTag(unmapped));
            tag.put("val", new IntArrayTag(mapped));
        } else if (shiftFormatSize < changedFormatSize && shiftFormatSize < plainFormatSize) {
            System.out.println(key + ": Storing as shifts");
            tag.put("id", new ByteTag(SHIFTS_ID));
            tag.put("size", new IntTag(mappings.length));

            final int[] shiftsAt = new int[result.shiftChanges()];
            final int[] shifts = new int[result.shiftChanges()];

            int index = 0;
            // Check the first entry
            if (mappings[0] != 0) {
                shiftsAt[0] = 0;
                shifts[0] = mappings[0];
                index++;
            }

            for (int id = 1; id < mappings.length; id++) {
                final int mappedId = mappings[id];
                if (mappedId != mappings[id - 1] + 1) {
                    shiftsAt[index] = id;
                    shifts[index] = mappedId - id;
                    index++;
                }
            }

            if (index != result.shiftChanges()) {
                throw new IllegalStateException("Index " + index + " does not equal number of changes " + result.shiftChanges());
            }

            tag.put("at", new IntArrayTag(shiftsAt));
            tag.put("val", new IntArrayTag(shifts));
        } else {
            System.out.println(key + ": Storing as direct values");
            tag.put("id", new ByteTag(DIRECT_ID));
            tag.put("val", new IntArrayTag(mappings));
        }
    }

    private static int approximateChangedFormatSize(final MappingsLoader.MappingsResult result) {
        // Length of two arrays + more approximate length for extra tags
        return (result.mappings().length - result.identityMappings()) * 2 + 10;
    }

    private static int approximateShiftFormatSize(final MappingsLoader.MappingsResult result) {
        // One entry in two arrays each time the id is not shifted by 1 from the last id + more approximate length for extra tags
        return result.shiftChanges() * 2 + 10;
    }
}
