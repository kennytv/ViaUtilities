package eu.kennytv.mappingsgenerator;

import java.io.File;
import java.net.URL;
import java.net.URLClassLoader;

public final class Main {

    private static final String[] ARGS = {"--reports"};

    public static void main(final String[] args) throws Exception {
        if (args.length != 2) {
            throw new IllegalArgumentException("Required args: path to server jar, version");
        }

        final String serverPath = args[0];
        final String version = args[1];
        MappingsGenerator.cleanup();

        System.out.println("Loading net.minecraft.data.Main class...");
        final ClassLoader loader = URLClassLoader.newInstance(
                new URL[]{new File(serverPath).toURI().toURL()},
                Main.class.getClassLoader()
        );

        final Object o = loader.loadClass("net.minecraft.data.Main").getConstructor().newInstance();
        final Object[] mainArgs = {ARGS};
        o.getClass().getDeclaredMethod("main", String[].class).invoke(null, mainArgs);

        MappingsGenerator.collectMappings(version);
    }
}
