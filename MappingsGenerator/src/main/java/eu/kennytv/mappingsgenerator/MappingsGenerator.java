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

        collectMappings("1.18-rc2");
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
            items.add(String.valueOf(itemsEntry.getValue().getAsJsonObject().getAsJsonPrimitive("protocol_id").getAsInt()), new JsonPrimitive(itemsEntry.getKey()));
        }

        // Sounds
        final JsonArray sounds = new JsonArray();
        viaMappings.add("sounds", sounds);
        int i = 0;
        for (final Map.Entry<String, JsonElement> soundEntry : object.getAsJsonObject("minecraft:sound_event").getAsJsonObject("entries").entrySet()) {
            if (soundEntry.getValue().getAsJsonObject().getAsJsonPrimitive("protocol_id").getAsInt() != i) {
                throw new IllegalStateException();
            }
            sounds.add(new JsonPrimitive(soundEntry.getKey().replace("minecraft:", "")));
            i++;
        }

        // Particles
        final JsonArray particles = new JsonArray();
        viaMappings.add("particles", particles);
        i = 0;
        for (final Map.Entry<String, JsonElement> particleEntry : object.getAsJsonObject("minecraft:particle_type").getAsJsonObject("entries").entrySet()) {
            if (particleEntry.getValue().getAsJsonObject().getAsJsonPrimitive("protocol_id").getAsInt() != i) {
                throw new IllegalStateException();
            }
            particles.add(new JsonPrimitive(particleEntry.getKey().replace("minecraft:", "")));
            i++;
        }

        // Block entities
        final JsonArray blockEntities = new JsonArray();
        viaMappings.add("blockentities", blockEntities);
        i = 0;
        for (final Map.Entry<String, JsonElement> particleEntry : object.getAsJsonObject("minecraft:block_entity_type").getAsJsonObject("entries").entrySet()) {
            if (particleEntry.getValue().getAsJsonObject().getAsJsonPrimitive("protocol_id").getAsInt() != i) {
                throw new IllegalStateException();
            }
            blockEntities.add(new JsonPrimitive(particleEntry.getKey().replace("minecraft:", "")));
            i++;
        }

        // Save
        new File("mappings").mkdir();
        try (final PrintWriter out = new PrintWriter("mappings/mapping-" + version + ".json")) {
            out.print(gson.toJson(viaMappings));
        }

        new File("logs").deleteOnExit();
        System.out.println("Done!");
    }
}