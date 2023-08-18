#! /bin/bash

rm Mappings/old_server.jar
mv Mappings/server.jar Mappings/old_server.jar
cp versions/server-"$1".jar Mappings/server.jar

cd Mappings
git checkout main
git fetch && git reset --hard origin/main

mvn clean package
mv target/MappingsGenerator-*.jar ./MappingsGenerator.jar
