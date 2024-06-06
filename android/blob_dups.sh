#!/bin/bash

# File containing the list of proprietary files
FILE="proprietary-files.txt"

# Check if the file exists
if [[ ! -f "$FILE" ]]; then
    echo "File $FILE does not exist."
    exit 1
fi

# Find and print duplicate lines, ignoring lines starting with #
echo "Duplicate lines in $FILE:"
awk '
    !/^#/ && NF {
        line = $0
        sub(/^- /, "", line)  # Remove leading - and space
        count[line]++
    }
    END {
        for (line in count) {
            if (count[line] > 1) {
                print count[line] " times: " line
            }
        }
    }
' "$FILE"

exit 0
