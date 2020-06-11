v=1.16-pre4
enigma=enigma-cli-0.19+build.195-all.jar
java -cp $enigma cuchaz.enigma.command.Main convert-mappings proguard mappings/$v.txt enigma mappings/$v
#java -cp $enigma cuchaz.enigma.command.Main deobfuscate versions/$v.jar deobf/$v.jar mappings/$v
#java -cp $enigma cuchaz.enigma.command.Main decompile PROCYON versions/$v.jar deobf/$v mappings/$v