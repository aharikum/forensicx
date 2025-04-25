# This script will help create a sample bindfs file system and mount it
# The structure for the file system will be as follows
#  /bindfs-mount/                
#   |-- tst1.txt                 
#   |-- tst2.txt                 
#   |-- new/
#       |-- tst3.txt


#!/bin/bash

SOURCE_DIR="$HOME/bindfs-source"
MOUNT_DIR="$HOME/bindfs-mount"

if mount | grep -q "$MOUNT_DIR"; then
    sudo umount "$MOUNT_DIR" 2>/dev/null
fi

# Remove old directories if they exist
rm -rf "$SOURCE_DIR" 2>/dev/null
rm -rf "$MOUNT_DIR" 2>/dev/null

mkdir -p "$SOURCE_DIR"
mkdir -p "$MOUNT_DIR"

sudo bindfs "$SOURCE_DIR" "$MOUNT_DIR"

echo "Test document 1" > "$MOUNT_DIR/tst1.txt"
echo "Test document 2" > "$MOUNT_DIR/tst2.txt"
mkdir -p "$MOUNT_DIR/new"
echo "Test document 3" > "$MOUNT_DIR/new/tst3.txt"

echo "BindFS mounted at $MOUNT_DIR"
