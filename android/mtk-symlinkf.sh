
#!/bin/bash
#
#  Apache License
#  Version 2.0, January 2004
#  http://www.apache.org/licenses/
#
#  Copyright 2024 Aryan Sinha <techyminati@outlook.com>
#  Copyright 2024 Riyon George <riyon336@gmail.com>
#

# Function to copy files from soc directories to their parent directories
symlinkfinder() {
    local soc="$1"
    local directories=(
        "vendor"
    )

    # Loop through each directory and copy files to their parent directories
    for dir in "${directories[@]}"; do
        find "$dir" -type f | while read -r blobs; do
            # Replace the soc portion of the symlink with an empty string
            symlink="${blobs/\/$soc}"

	    # Remove trailing soc
            symlink="${symlink%.$soc}"

	    # Check if the symlink is different from the file path and if it doesn't match the file path without the soc suffix
            if [ "$symlink" != "$blobs" ] && [ "${blobs%.$soc}" != "$symlink" ]; then
                echo "${blobs};SYMLINK=${symlink}"
            fi
        done
    done
}

# Main function
main() {
    if [ "$#" -ne 1 ]; then
        echo "Usage: $0 <soc>"
        exit 1
    fi

    soc="$1"
    symlinkfinder "$soc"
}

# Run the main function with the provided argument
main "$@"