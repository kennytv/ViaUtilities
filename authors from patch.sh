#!/bin/bash

# Input patch file
PATCH_FILE="patch.txt"

# Extract all From: lines in the format "From: Name <email>"
# Then normalize and deduplicate
COAUTHORS=$(grep -oP '^From:\s+\K.*<[^>]+>' "$PATCH_FILE" | sort -u)

# Output in "Co-authored-by: Name <email>" format
while read -r author; do
    echo "Co-authored-by: $author"
done <<< "$COAUTHORS"