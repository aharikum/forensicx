# This script will help create a sample encrypted encfs and mount it
# The mount is created with the password "demo"
# The structure for the file system will be as follows
#  /encfsfs-mount/                
#   |-- secret1.txt                 
#   |-- secret2.txt                 
#   |-- private/
#       |-- secret3.txt

#!/bin/bash

ENCRYPTED_DIR="$HOME/encfs-encrypted"
MOUNT_DIR="$HOME/encfs-mount"
PASSWORD="demo"

if mount | grep -q "$MOUNT_DIR"; then
    fusermount -u "$MOUNT_DIR" 2>/dev/null
fi

rm -rf "$ENCRYPTED_DIR" 2>/dev/null
rm -rf "$MOUNT_DIR" 2>/dev/null


mkdir -p "$ENCRYPTED_DIR"
mkdir -p "$MOUNT_DIR"

echo "$PASSWORD" | encfs --standard "$ENCRYPTED_DIR" "$MOUNT_DIR" --extpass="echo $PASSWORD"

echo "Secret document 1" > "$MOUNT_DIR/secret1.txt"
echo "Secret document 2" > "$MOUNT_DIR/secret2.txt"
mkdir -p "$MOUNT_DIR/private"
echo "Secret document 3" > "$MOUNT_DIR/private/secret3.txt"

echo "EncFS mounted at $MOUNT_DIR"
echo "Password is: $PASSWORD"
