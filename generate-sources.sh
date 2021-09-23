#! /bin/bash

platform=$1
v=$2
name=$platform-$v
enigma=enigma-cli.jar

# Generate Enigma mapping folder
if [ ! -d sources/$name-mapping ]
then
	echo "===== Generating Enigma mappings file"
	java -cp $enigma cuchaz.enigma.command.Main convert-mappings proguard sources/$name.txt enigma_file sources/$name-mapping
fi

if [ ! -d sources/$name ]
then mkdir sources/$name
fi

# Export mapped sources
# 8 gigabytes of ram are not enough, even for the server lololol
java -Xms4096M -Xmx15000M -cp $enigma cuchaz.enigma.command.Main decompile CFR versions/$name.jar sources/$name sources/$name-mapping

# Cleanup
#rm sources/$name-mapping
#rm sources/$name.txt