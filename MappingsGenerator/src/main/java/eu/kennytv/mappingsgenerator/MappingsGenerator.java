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
        final JsonObject blockstates = new JsonObject();
        final JsonObject blocks = new JsonObject();
        viaMappings.add("blockstates", blockstates);
        viaMappings.add("blocks", blocks);
        String lastBlock = "";
        int id = 0;
        for (final Map.Entry<String, JsonElement> blocksEntry : object.entrySet()) {
            final JsonObject block = blocksEntry.getValue().getAsJsonObject();
            final JsonArray states = block.getAsJsonArray("states");
            for (final JsonElement state : states) {
                final StringBuilder value = new StringBuilder(blocksEntry.getKey());
                if (!lastBlock.equals(blocksEntry.getKey())) {
                    lastBlock = blocksEntry.getKey();
                    blocks.add(Integer.toString(id++), new JsonPrimitive(lastBlock.replace("minecraft:", "")));
                }
                if (state.getAsJsonObject().has("properties")) {
                    value.append('[');
                    final JsonObject properties = state.getAsJsonObject().getAsJsonObject("properties");
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
                blockstates.add(state.getAsJsonObject().get("id").getAsString(), new JsonPrimitive(value.toString()));
            }
        }

        content = new String(Files.readAllBytes(new File("generated/reports/registries.json").toPath()));
        object = gson.fromJson(content, JsonObject.class);

        // Items
        final JsonObject items = new JsonObject();
        viaMappings.add("items", items);
        for (final Map.Entry<String, JsonElement> itemsEntry : object.getAsJsonObject("minecraft:item").getAsJsonObject("entries").entrySet()) {
            final int protocolId = itemsEntry.getValue().getAsJsonObject().getAsJsonPrimitive("protocol_id").getAsInt();
            items.add(String.valueOf(protocolId), new JsonPrimitive(itemsEntry.getKey()));
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
        final JsonArray array = new JsonArray();
        mappings.add(mappingsKey, array);
        int i = 0;
        for (final Map.Entry<String, JsonElement> entry : registry.getAsJsonObject(registryKey).getAsJsonObject("entries").entrySet()) {
            final int protocolId = entry.getValue().getAsJsonObject().getAsJsonPrimitive("protocol_id").getAsInt();
            if (protocolId != i) {
                throw new IllegalStateException("Expected id " + i + " to follow, got " + protocolId + " in " + registryKey);
            }

            array.add(new JsonPrimitive(removeNamespace ? entry.getKey().replace("minecraft:", "") : entry.getKey()));
            i++;
        }
    }
}