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
package eu.kennytv.mappingsgenerator.extra;

import com.github.steveice10.opennbt.NBTIO;
import com.github.steveice10.opennbt.tag.builtin.CompoundTag;
import com.github.steveice10.opennbt.tag.builtin.ListTag;
import com.github.steveice10.opennbt.tag.builtin.StringTag;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import eu.kennytv.mappingsgenerator.MappingsLoader;
import eu.kennytv.mappingsgenerator.MappingsOptimizer;
import java.io.File;
import java.io.IOException;

public final class BlockStates1_13 {

    public static void main(final String[] args) throws IOException {
        final JsonArray blockstates = MappingsLoader.load("mapping-1.13.json").getAsJsonArray("blockstates");
        final CompoundTag tag = new CompoundTag();
        final ListTag list = new ListTag(StringTag.class);
        for (final JsonElement element : blockstates) {
            list.add(new StringTag(element.getAsString()));
        }
        tag.put("blockstates", list);
        NBTIO.writeFile(tag, new File(MappingsOptimizer.OUTPUT_DIR, "blockstates-1.13.nbt"), false, false);
    }
}
