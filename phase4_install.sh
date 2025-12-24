#!/bin/bash

# Phase 4: Installation Script for Acer Chromebook R11 (Cyan) -> ChromeOS (Rammus)
# This script automates the "Execute Commands" section of the guide.
# Usage: Place this script in the same folder as your downloaded Brunch and ChromeOS files (usually ~/Downloads) and run it.

set -e # Exit on error

echo "--- Phase 4: ChromeOS Installation Script ---"

# 1. Check for required files
echo "Checking for files..."

# Find Brunch file
BRUNCH_FILE=$(ls brunch_r*.tar.gz 2>/dev/null | head -n 1)
if [ -z "$BRUNCH_FILE" ]; then
    echo "Error: Brunch file (brunch_r*.tar.gz) not found in current directory."
    echo "Please ensure you are in the directory with the downloaded files."
    exit 1
fi

# Find Recovery Image
RECOVERY_ZIP=$(ls chromeos_*.zip 2>/dev/null | head -n 1)
if [ -z "$RECOVERY_ZIP" ]; then
    echo "Error: Recovery image (chromeos_*.zip) not found in current directory."
    echo "Please ensure you are in the directory with the downloaded files."
    exit 1
fi

echo "Found Brunch: $BRUNCH_FILE"
echo "Found Recovery: $RECOVERY_ZIP"

# Step A: Extract Brunch
echo "Step A: Extracting Brunch tools..."
tar -zxvf "$BRUNCH_FILE"

# Step B: Unzip Recovery Image
echo "Step B: Unzipping Recovery Image..."
unzip -o "$RECOVERY_ZIP"

# Step C: Rename Recovery Image
# Find the .bin file extracted
RECOVERY_BIN=$(ls chromeos_*.bin 2>/dev/null | head -n 1)
if [ -z "$RECOVERY_BIN" ]; then
    if [ -f "rammus.bin" ]; then
        echo "rammus.bin already exists, skipping rename."
    else
        echo "Error: Could not find extracted .bin file."
        exit 1
    fi
else
    echo "Step C: Renaming $RECOVERY_BIN to rammus.bin..."
    mv "$RECOVERY_BIN" rammus.bin
fi

# Step D: Identify Hard Drive
echo "Step D: Identifying Hard Drive..."
lsblk -e7

TARGET_DISK="/dev/mmcblk0"

# Check if the default target exists
if [ ! -b "$TARGET_DISK" ]; then
    echo "Warning: Default target $TARGET_DISK not found."
    echo "Available disks:"
    lsblk -d -n -o NAME,SIZE,TYPE | grep disk
    read -p "Please enter the target drive path (e.g., /dev/sda): " TARGET_DISK
else
    echo "Targeting default internal storage: $TARGET_DISK"
fi

# Step E: Installation
echo "Step E: Running ChromeOS Installation..."
echo "Executing: sudo bash chromeos-install.sh -src rammus.bin -dst $TARGET_DISK"
echo "IMPORTANT: You will be asked to confirm. Type 'yes' when prompted."

sudo bash chromeos-install.sh -src rammus.bin -dst "$TARGET_DISK"

echo "--- Installation Complete ---"
echo "Please shut down, remove the USB drive, and power on your device."
