package eu.kennytv.mappingsgenerator;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonPrimitive;

import java.io.File;
import java.io.IOException;
import java.io.PrintWriter;
import java.nio.file.Files;
import java.util.Map;
import java.util.TreeMap;

public final class MappingsGenerator {

    /**
     * For in-IDE execution.
     */
    public static void main(final String[] args) throws Exception {
        cleanup();

        try {
            // Server jar bundle since 21w39a
            System.setProperty("bundlerMainClass", "net.minecraft.data.Main");
            Class.forName("net.minecraft.bundler.Main").getDeclaredMethod("main", String[].class).invoke(null, (Object) new String[]{"--reports"});
            Main.waitForServerMain();
        } catch (final ClassNotFoundException ignored) {
            final Class<?> mainClass = Class.forName("net.minecraft.data.Main");
            mainClass.getDeclaredMethod("main", String[].class).invoke(null, (Object) new String[]{"--reports"});
        }

        collectMappings("1.19");
    }

    public static void cleanup() {
        delete(new File("generated"));
        delete(new File("logs"));
    }

    public static void delete(final File file) {
        if (!file.exists()) return;
        if (file.isDirectory()) {
            for (final File f : file.listFiles()) {
                delete(f);
            }
        }

        file.delete();
    }

    public static void collectMappings(final String version) throws IOException {
        System.out.println("Beginning mapping collection...");
        String content = new String(Files.readAllBytes(new File("generated/reports/blocks.json").toPath()));

        final Gson gson = new GsonBuilder().setPrettyPrinting().disableHtmlEscaping().create();
        JsonObject object = gson.fromJson(content, JsonObject.class);

        final JsonObject viaMappings = new JsonObject();

        // Blocks and blockstates
        final Map<Integer, String> blockstatesById = new TreeMap<>();
        for (final Map.Entry<String, JsonElement> blocksEntry : object.entrySet()) {
            final JsonObject block = blocksEntry.getValue().getAsJsonObject();
            final JsonArray states = block.getAsJsonArray("states");
            for (final JsonElement state : states) {
                final JsonObject stateObject = state.getAsJsonObject();
                final int id = stateObject.getAsJsonPrimitive("id").getAsInt();
                if (blockstatesById.containsKey(id)) {
                    throw new IllegalArgumentException("Duplicate blockstate id: " + id);
                }

                final StringBuilder value = new StringBuilder(blocksEntry.getKey());
                if (stateObject.has("properties")) {
                    value.append('[');
                    final JsonObject properties = stateObject.getAsJsonObject("properties");
                    boolean first = true;
                    for (final Map.Entry<String, JsonElement> propertyEntry : properties.entrySet()) {
                        if (first) {
                            first = false;
                        } else {
                            value.append(',');
                        }
                        value.append(propertyEntry.getKey()).append('=').append(propertyEntry.getValue().getAsJsonPrimitive().getAsString());
                    }
                    value.append(']');
                }
                blockstatesById.put(id, value.toString());
            }
        }

        final JsonObject blockstates = new JsonObject();
        final JsonObject blocks = new JsonObject();
        viaMappings.add("blockstates", blockstates);
        viaMappings.add("blocks", blocks);

        String lastBlock = "";
        int blockId = 0;
        for (final Map.Entry<Integer, String> entry : blockstatesById.entrySet()) {
            final String idString = Integer.toString(entry.getKey());
            final String blockstate = entry.getValue();
            blockstates.addProperty(idString, blockstate);

            final String block = blockstate.split("\\[", 2)[0];
            if (!lastBlock.equals(block)) {
                lastBlock = block;
                blocks.add(Integer.toString(blockId++), new JsonPrimitive(lastBlock.replace("minecraft:", "")));
            }
        }

        content = new String(Files.readAllBytes(new File("generated/reports/registries.json").toPath()));
        object = gson.fromJson(content, JsonObject.class);

        // Items
        final Map<Integer, String> itemsById = new TreeMap<>();
        final JsonObject entries = object.getAsJsonObject("minecraft:item").getAsJsonObject("entries");
        for (final Map.Entry<String, JsonElement> itemsEntry : entries.entrySet()) {
            final int protocolId = itemsEntry.getValue().getAsJsonObject().getAsJsonPrimitive("protocol_id").getAsInt();
            itemsById.put(protocolId, itemsEntry.getKey());
        }

        final JsonObject items = new JsonObject();
        viaMappings.add("items", items);
        for (final Map.Entry<Integer, String> entry : itemsById.entrySet()) {
            items.addProperty(Integer.toString(entry.getKey()), entry.getValue());
        }

        addArray(viaMappings, object, "minecraft:sound_event", "sounds", true);
        addArray(viaMappings, object, "minecraft:particle_type", "particles", true);
        addArray(viaMappings, object, "minecraft:block_entity_type", "blockentities", true);
        addArray(viaMappings, object, "minecraft:command_argument_type", "argumenttypes");
        addArray(viaMappings, object, "minecraft:enchantment", "enchantments");
        addArray(viaMappings, object, "minecraft:entity_type", "entities");
        addArray(viaMappings, object, "minecraft:motive", "paintings");
        addArray(viaMappings, object, "minecraft:painting_variant", "paintings");

        // Save
        new File("mappings").mkdir();
        try (final PrintWriter out = new PrintWriter("mappings/mapping-" + version + ".json")) {
            out.print(gson.toJson(viaMappings));
        }

        new File("logs").deleteOnExit();
        System.out.println("Done!");
    }

    private static void addArray(final JsonObject mappings, final JsonObject registry, final String registryKey, final String mappingsKey) {
        addArray(mappings, registry, registryKey, mappingsKey, false);
    }

    private static void addArray(final JsonObject mappings, final JsonObject registry, final String registryKey, final String mappingsKey, final boolean removeNamespace) {
        if (!registry.has(registryKey)) {
            System.out.println("Ignoring missing registry: " + registryKey);
            return;
        }

        System.out.println("Collecting " + registryKey + "...");
        final JsonObject entries = registry.getAsJsonObject(registryKey).getAsJsonObject("entries");
        final String[] keys = new String[entries.size()];
        for (final Map.Entry<String, JsonElement> entry : entries.entrySet()) {
            final int protocolId = entry.getValue().getAsJsonObject().getAsJsonPrimitive("protocol_id").getAsInt();
            if (protocolId < 0 || protocolId >= keys.length) {
                throw new IllegalArgumentException("Out of bounds protocol id: " + protocolId + " in " + registryKey);
            }
            if (keys[protocolId] != null) {
                throw new IllegalArgumentException("Duplicate protocol id: " + protocolId + " in " + registryKey);
            }

            keys[protocolId] = removeNamespace ? entry.getKey().replace("minecraft:", "") : entry.getKey();
        }

        final JsonArray array = new JsonArray();
        mappings.add(mappingsKey, array);
        for (final String key : keys) {
            array.add(new JsonPrimitive(key));
        }
    }
}