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

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import it.unimi.dsi.fastutil.ints.Int2IntLinkedOpenHashMap;
import it.unimi.dsi.fastutil.ints.Int2IntMap;
import it.unimi.dsi.fastutil.objects.Object2IntMap;
import it.unimi.dsi.fastutil.objects.Object2IntOpenHashMap;
import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.util.Map;
import org.jetbrains.annotations.Nullable;

public final class MappingsLoader {

    private static final Gson GSON = new GsonBuilder().disableHtmlEscaping().create();

    /**
     * Loads and return the json mappings file.
     *
     * @param name name of the mappings file
     * @return the mappings file as a JsonObject, or null if it does not exist
     */
    public static @Nullable JsonObject load(final String name) throws IOException {
        final File file = new File("mappings", name);
        if (!file.exists()) {
            return null;
        }

        final String content = Files.readString(file.toPath());
        return GSON.fromJson(content, JsonObject.class);
    }

    /**
     * Returns a mappings result with int to int array mappings.
     *
     * @param unmappedIdentifiers array of unmapped identifiers
     * @param mappedIdentifiers   array of mapped identifiers
     * @param diffIdentifiers     diff identifiers
     * @param warnOnMissing       whether to warn on missing mappings
     * @return mappings result with int to int array mappings
     */
    public static MappingsResult map(final JsonArray unmappedIdentifiers, final JsonArray mappedIdentifiers, @Nullable final JsonObject diffIdentifiers, final boolean warnOnMissing) {
        final int[] output = new int[unmappedIdentifiers.size()];
        final Object2IntMap<String> newIdentifierMap = MappingsLoader.arrayToMap(mappedIdentifiers);
        int emptyMappings = 0;
        int identityMappings = 0;
        int shiftChanges = 0;
        for (int id = 0; id < unmappedIdentifiers.size(); id++) {
            final JsonElement unmappedIdentifier = unmappedIdentifiers.get(id);
            final int mappedId = mapEntry(id, unmappedIdentifier.getAsString(), newIdentifierMap, diffIdentifiers, warnOnMissing);
            if (mappedId != -1) {
                output[id] = mappedId;
                if (mappedId == id) {
                    identityMappings++;
                }
            } else {
                emptyMappings++;
            }

            // Check the first entry/if the shift changed
            if (id == 0 && mappedId != 0
                    || id != 0 && mappedId != output[id - 1] + 1) {
                shiftChanges++;
            }
        }
        return new MappingsResult(output, mappedIdentifiers.size(), emptyMappings, identityMappings, shiftChanges);
    }

    /**
     * Returns a mappings result of two identifier objects keyed by their int id.
     *
     * @param unmappedIdentifiers object of unmapped identifiers, keyed by their int id
     * @param mappedIdentifiers   object of mapped identifiers, keyed by their int id
     * @param diffIdentifiers     diff identifiers
     * @param warnOnMissing       whether to warn on missing mappings
     * @return mappings result
     */
    public static Int2IntMap map(final JsonObject unmappedIdentifiers, final JsonObject mappedIdentifiers, @Nullable final JsonObject diffIdentifiers, final boolean warnOnMissing) {
        final Int2IntMap output = new Int2IntLinkedOpenHashMap();
        output.defaultReturnValue(-1);
        final Object2IntMap<String> newIdentifierMap = MappingsLoader.indexedObjectToMap(mappedIdentifiers);
        for (final Map.Entry<String, JsonElement> entry : unmappedIdentifiers.entrySet()) {
            final int id = Integer.parseInt(entry.getKey());
            final int mappedId = mapEntry(id, entry.getValue().getAsString(), newIdentifierMap, diffIdentifiers, warnOnMissing);
            output.put(id, mappedId);
        }
        return output;
    }

    /**
     * Returns the mapped id of the given entry, or -1 if not found.
     *
     * @param id                id of the entry
     * @param value             value of the entry
     * @param mappedIdentifiers mapped identifiers
     * @param diffIdentifiers   diff identifiers
     * @param warnOnMissing     whether to warn on missing mappings
     * @return mapped id, or -1 if it was not found
     */
    private static int mapEntry(final int id, final String value, final Object2IntMap<String> mappedIdentifiers, @Nullable final JsonObject diffIdentifiers, final boolean warnOnMissing) {
        int mappedId = mappedIdentifiers.getInt(value);
        if (mappedId == -1) {
            // Search in diff mappings
            if (diffIdentifiers != null) {
                JsonElement diffElement = diffIdentifiers.get(value);
                if (diffElement != null || (diffElement = diffIdentifiers.get(Integer.toString(id))) != null) {
                    final String mappedName = diffElement.getAsString();
                    if (mappedName.isEmpty()) {
                        return -1; // "empty" remaps without warnings
                    }

                    mappedId = mappedIdentifiers.getInt(mappedName);

                }
            }
            if (mappedId == -1 && warnOnMissing) {
                System.out.println("No key for " + value + " :( ");
            }
        }
        return mappedId;
    }

    /**
     * Returns a map of the object entries hashed by their id value.
     *
     * @param object json object
     * @return map with indexes hashed by their id value
     */
    public static Object2IntMap<String> indexedObjectToMap(final JsonObject object) {
        final Object2IntMap<String> map = new Object2IntOpenHashMap<>(object.size());
        map.defaultReturnValue(-1);
        for (final Map.Entry<String, JsonElement> entry : object.entrySet()) {
            map.put(entry.getValue().getAsString(), Integer.parseInt(entry.getKey()));
        }
        return map;
    }

    /**
     * Returns a map of the array entries hashed by their id value.
     *
     * @param array json array
     * @return map with indexes hashed by their id value
     */
    public static Object2IntMap<String> arrayToMap(final JsonArray array) {
        final Object2IntMap<String> map = new Object2IntOpenHashMap<>(array.size());
        map.defaultReturnValue(-1);
        for (int i = 0; i < array.size(); i++) {
            map.put(array.get(i).getAsString(), i);
        }
        return map;
    }

    /**
     * Result of a mapping data loader operation.
     *
     * @param mappings         int to int id mappings
     * @param mappedSize       number of mapped ids, most likely greater than the length of the mappings array
     * @param emptyMappings    number of empty (-1) mappings
     * @param identityMappings number of identity mappings
     * @param shiftChanges     number of shift changes where a mapped id is not the last mapped id + 1
     */
    record MappingsResult(int[] mappings, int mappedSize, int emptyMappings, int identityMappings, int shiftChanges) {
    }
}
