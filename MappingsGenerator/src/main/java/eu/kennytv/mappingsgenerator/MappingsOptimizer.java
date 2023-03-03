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
import com.github.steveice10.opennbt.tag.builtin.CompoundTag;
import com.github.steveice10.opennbt.tag.builtin.IntArrayTag;
import com.github.steveice10.opennbt.tag.builtin.ListTag;
import com.github.steveice10.opennbt.tag.builtin.StringTag;
import com.github.steveice10.opennbt.tag.builtin.Tag;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import it.unimi.dsi.fastutil.ints.Int2IntMap;
import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import org.jetbrains.annotations.Nullable;

public final class MappingsOptimizer {

    private static final String DILL_FILE_FORMAT = "mappingdiff-%sto%s.json";
    private static final String MAPPING_FILE_FORMAT = "mapping-%s.json";
    private static final String OUTPUT_FILE_FORMAT = "mappings-%sto%s.nbt";
    private static final File MAPPINGS_DIR = new File("mappings");
    private static final boolean RUN_ALL = true;

    public static void main(final String[] args) throws IOException {
        if (RUN_ALL) {
            runAll();
            return;
        }

        final String from = args.length == 2 ? args[0] : "1.19.3";
        final String to = args.length == 2 ? args[1] : "1.19.4";
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
        if (unmappedObject == null) {
            throw new IllegalArgumentException("Mapping file for version " + from + " does not exist");
        }
        if (mappedObject == null) {
            throw new IllegalArgumentException("Mapping file for version " + to + " does not exist");
        }

        final JsonObject diffObject = MappingsLoader.load(DILL_FILE_FORMAT.formatted(from, to));

        final CompoundTag tag = new CompoundTag();
        mappings(tag, unmappedObject, mappedObject, diffObject, true, "blockstates");
        mappings(tag, unmappedObject, mappedObject, diffObject, true, "blocks");
        mappings(tag, unmappedObject, mappedObject, diffObject, true, "items");
        mappings(tag, unmappedObject, mappedObject, diffObject, true, "sounds");
        mappings(tag, unmappedObject, mappedObject, diffObject, true, "blockentities");
        mappings(tag, unmappedObject, mappedObject, diffObject, true, "enchantments");
        mappings(tag, unmappedObject, mappedObject, diffObject, true, "paintings");
        fullMappings(tag, unmappedObject, mappedObject, diffObject, true, false, "entities");
        fullMappings(tag, unmappedObject, mappedObject, diffObject, true, true, "particles");
        fullMappings(tag, unmappedObject, mappedObject, diffObject, true, true, "argumenttypes");

        NBTIO.writeFile(tag, new File(MAPPINGS_DIR, OUTPUT_FILE_FORMAT.formatted(from, to)), false, false);
    }

    private static void optimizeAndSaveOhSoSpecial1_12AsNBT() throws IOException {
        final JsonObject unmappedObject = MappingsLoader.load("mapping-1.12.json");
        final JsonObject mappedObject = MappingsLoader.load("mapping-1.13.json");

        final CompoundTag tag = new CompoundTag();
        cursedMappings(tag, unmappedObject, mappedObject, "blockstates");
        cursedMappings(tag, unmappedObject, mappedObject, "items");
        mappings(tag, unmappedObject, mappedObject, null, true, "sounds");

        NBTIO.writeFile(tag, new File(MAPPINGS_DIR, "mappings-1.12to1.13.nbt"), false, false);
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
     * @param tag            tag to write to
     * @param unmappedObject unmapped mappings object
     * @param mappedObject   mapped mappings object
     * @param diffMappings   diff mappings object
     * @param warnOnMissing  whether to warn on missing mappings
     * @param key            to read from and write to
     */
    private static void mappings(
            final CompoundTag tag,
            final JsonObject unmappedObject,
            final JsonObject mappedObject,
            @Nullable final JsonObject diffMappings,
            final boolean warnOnMissing,
            final String key
    ) {
        if (!unmappedObject.has(key) || !mappedObject.has(key)) {
            return;
        }

        final JsonArray unmappedIdentifiers = unmappedObject.getAsJsonArray(key);
        final JsonArray mappedIdentifiers = mappedObject.getAsJsonArray(key);
        if (unmappedIdentifiers.equals(mappedIdentifiers)) {
            System.out.println(key + ": Skipped");
            return;
        }

        final JsonObject diffIdentifiers = diffMappings != null ? diffMappings.getAsJsonObject(key) : null;
        final MappingsLoader.MappingsResult result = MappingsLoader.map(unmappedIdentifiers, mappedIdentifiers, diffIdentifiers, warnOnMissing);
        store(result, tag, key);
    }

    /**
     * Reads mappings from the unmapped and mapped objects and writes them to the nbt tag.
     * Also writes the unmapped identifiers to the tag.
     *
     * @param tag            tag to write to
     * @param unmappedObject unmapped mappings object
     * @param mappedObject   mapped mappings object
     * @param diffMappings   diff mappings object
     * @param warnOnMissing  whether to warn on missing mappings
     * @param key            to read from and write to
     */
    private static void fullMappings(
            final CompoundTag tag,
            final JsonObject unmappedObject,
            final JsonObject mappedObject,
            @Nullable final JsonObject diffMappings,
            final boolean warnOnMissing,
            final boolean alwaysProvideIdentifiers,
            final String key
    ) {
        if (!unmappedObject.has(key)) {
            return;
        }
        if (!unmappedObject.get(key).isJsonArray() || !mappedObject.get(key).isJsonArray()) {
            System.out.println("Skipping " + key + " as it's not an array");
            return;
        }

        final JsonArray unmappedIdentifiers = unmappedObject.getAsJsonArray(key);
        if (alwaysProvideIdentifiers) {
            final List<Tag> identifiers = new ArrayList<>();
            for (final JsonElement identifier : unmappedIdentifiers) {
                identifiers.add(new StringTag(identifier.getAsString()));
            }
            tag.put(key + "-identifiers", new ListTag(identifiers));
        }

        mappings(tag, unmappedObject, mappedObject, diffMappings, warnOnMissing, key);
    }

    private static void cursedMappings(final CompoundTag tag, final JsonObject unmappedObject, final JsonObject mappedObject, final String key) {
        final Int2IntMap map = MappingsLoader.map(
                unmappedObject.getAsJsonObject(key),
                toJsonObject(mappedObject.getAsJsonArray(key)),
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

        changedTag.put("changed", new IntArrayTag(unmapped));
        changedTag.put("mapped", new IntArrayTag(mapped));
        tag.put(key, changedTag);
    }

    /**
     * Writes an int to int mappings result to the ntb tag.
     *
     * @param result result with int to int mappings
     * @param tag    tag to write to
     * @param key    key to write to
     */
    private static void store(final MappingsLoader.MappingsResult result, final CompoundTag tag, final String key) {
        final int[] mappings = result.mappings();
        final int numberOfChanges = mappings.length - result.identityMappings();
        if (numberOfChanges == 0 && result.emptyMappings() == 0) {
            System.out.println(key + ": Skipped due to no relevant id changes");
            return;
        }

        if (numberOfChanges * 2 < mappings.length) {
            System.out.println(key + ": Storing in alternative format");
            // Put two intarrays of only changed ids instead of adding an entry for every single identifier
            final CompoundTag changedTag = new CompoundTag();
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

            changedTag.put("changed", new IntArrayTag(unmapped));
            changedTag.put("mapped", new IntArrayTag(mapped));
            tag.put(key, changedTag);
        } else {
            tag.put(key, new IntArrayTag(mappings));
        }
    }

    private static JsonObject toJsonObject(final JsonArray array) {
        final JsonObject object = new JsonObject();
        for (int i = 0; i < array.size(); i++) {
            final JsonElement element = array.get(i);
            object.add(Integer.toString(i), element);
        }
        return object;
    }
}
