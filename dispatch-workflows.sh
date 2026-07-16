#! /bin/bash

gh workflow run check.yml --repo ViaVersion/Mappings
gh workflow run main.yml --repo kennytv/MCSources

sleep 5
echo "Mappings:"
gh run list --repo ViaVersion/Mappings --workflow check.yml --limit 1

run_id=$(gh run list --repo kennytv/MCSources --workflow main.yml --limit 1 --json databaseId --jq '.[0].databaseId')
echo "Watching MCSources run $run_id:"
gh run watch "$run_id" --repo kennytv/MCSources --exit-status
