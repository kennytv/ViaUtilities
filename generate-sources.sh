#! /bin/bash

platform=$1
v=$2
enigma=enigma-cli.jar

# Generate Enigma mapping folder
java -cp $enigma cuchaz.enigma.command.Main convert-mappings proguard sources/$platform-$v.txt enigma sources/$platform-$v-mapping

# Compile mapped jar
# java -cp $enigma cuchaz.enigma.command.Main deobfuscate versions/$platform-$v.jar sources/$platform-$v-deobf.jar sources/$platform-$v-mapping

if [ ! -d sources/$platform-$v ]
then mkdir sources/$platform-$v
fi

# Export mapped sources
java -cp $enigma cuchaz.enigma.command.Main decompile PROCYON versions/$platform-$v.jar sources/$platform-$v sources/$platform-$v-mapping

# Cleanup
rm -r sources/$platform-$v-mapping
#rm sources/$platform-$v.txt