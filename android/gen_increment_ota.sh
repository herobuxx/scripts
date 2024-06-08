#!/bin/bash

#
# Copyright (C) 2024 Lilium Project
#
# SPDX-License-Identifier: Apache-2.0
#

# Initial variables
OLD_BUILD_PATH=$1
NEW_BUILD_PATH=$2
KEY_PATH=$3
OUT_FILE_NAME=$(basename "$NEW_BUILD_PATH" .zip)
AOSP_DIR=$(pwd)

# Define Releasetool Firectory
RELEASETOOLS_DIR="$AOSP_DIR/build/tools/releasetools"

# Check if all required arguments are provided
if [ $# -ne 3 ]; then
    echo "Usage: $0 <old_build_path> <new_build_path> <key_path>"
    exit 1
fi

# Check if envsetup.sh exists in the AOSP build directory
AOSP_BUILD_SCRIPT="$AOSP_DIR/build/envsetup.sh"
if [ ! -f "$AOSP_BUILD_SCRIPT" ]; then
    echo "Error: The envsetup.sh file does not exist in the AOSP build directory."
    exit 1
fi

# Extracting target files
mkdir working working/old working/new
unzip -q "$OLD_BUILD_PATH" -d working/old
unzip -q "$NEW_BUILD_PATH" -d working/new

# Generating target files packages
python "$RELEASETOOLS_DIR/ota_from_target_files.py" -p out/host/linux-x86 -k "$KEY_PATH" -d -v working/old old-target_filest.zip
python "$RELEASETOOLS_DIR/ota_from_target_files.py" -p out/host/linux-x86 -k "$KEY_PATH" -d -v working/new new-target_files.zip

# Creating the incremental OTA package
python "$RELEASETOOLS_DIR/ota_from_target_files" -i working/old/old-target_files.zip working/new/new-target_files.zip working/incremental_ota_package.zip

# Signing the OTA package
sign_target_files_apks -o -d "$KEY_PATH" incremental_ota_package.zip working/${OUT_FILE_NAME}-increment.zip

# Clean up temporary files
rm -rf working/old working/new

echo "Incremental OTA package created: working/${OUT_FILE_NAME}-increment.zip"
