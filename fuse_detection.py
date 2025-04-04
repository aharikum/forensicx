#!/usr/bin/env python3
"""
FUSE Filesystem Detection Module

References:
- https://www.kernel.org/doc/Documentation/filesystems/fuse.txt
- https://github.com/libfuse/libfuse/wiki
"""

import os
import re
import subprocess
import logging

# Global variables
PROC_MOUNTS_PATH = "/proc/mounts"
FUSE_TYPES = {
    "encfs": ["encfs", "encrypted"],
    "bindfs": ["bindfs"],
    "generic": ["fuse"]
}

logger = logging.getLogger(__name__)

def detect_fuse_filesystems():
    """
    Detect FUSE filesystems using multiple methods: /proc/mounts and df commands
    """
    mounts = []
    mount_points = set()  # Track mount points to avoid duplicates

    # Method 1: Parse /proc/mounts file
    # /proc/mounts format: device_path mount_point fs_type mount_options dump_freq pass_num
    # Example line: fusectl /sys/fs/fuse/connections fusectl rw,relatime 0 0
    try:
        with open(PROC_MOUNTS_PATH, 'r') as f:
            lines = f.readlines()
            
        logger.debug(f"Checking {PROC_MOUNTS_PATH} for FUSE filesystems")
        for line in lines:
            if 'fuse' in line.lower():
                parts = line.split()
                if len(parts) >= 3:
                    source, mount_point, fs_type = parts[0], parts[1], parts[2]
                    fuse_type = _determine_fuse_type(line)     
                    mount_info = {
                        'source': source,
                        'mount_point': mount_point,
                        'fs_type': fs_type,
                        'fuse_type': fuse_type,
                        'detection_method': 'proc_mounts'
                    }
                    mounts.append(mount_info)
                    mount_points.add(mount_point)
                    logger.debug(f"Found FUSE mount: {mount_point} ({fuse_type})")
    except Exception as e:
        logger.error(f"Error reading {PROC_MOUNTS_PATH}: {e}")
    
    # Method 2: Use df -T command
    # df -T output format: Filesystem Type 1K-blocks Used Available Use% Mounted_on
    # Example: /dev/sda1 fuse.ntfs-3g 512000 123456 388544 25% /mnt/windows
    try:
        logger.debug("Running df -T command to detect FUSE filesystems")
        result = subprocess.run(['df', '-T'], capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            # Skip header line
            for line in lines[1:]:
                if 'fuse' in line.lower():
                    parts = line.split()
                    if len(parts) >= 7:
                        # df output columns: Filesystem Type 1K-blocks Used Available Use% Mounted-on
                        filesystem, fs_type = parts[0], parts[1]
                        mount_point = parts[6]
                        
                        # Skip if already found in /proc/mounts
                        if mount_point in mount_points:
                            logger.debug(f"Skip duplicate mount point: {mount_point}")
                            continue
                        
                        fuse_type = _determine_fuse_type(line)
                        
                        mount_info = {
                            'source': filesystem,
                            'mount_point': mount_point,
                            'fs_type': fs_type,
                            'fuse_type': fuse_type,
                            'detection_method': 'df_command'
                        }
                        mounts.append(mount_info)
                        mount_points.add(mount_point)
                        logger.debug(f"Found FUSE mount via df: {mount_point} ({fuse_type})")
        else:
            logger.warning(f"df command failed with error: {result.stderr}")
    except Exception as e:
        logger.error(f"Error running df command: {e}")
    
    if not mounts:
        logger.warning("No FUSE filesystems detected using any method")
    else:
        logger.info(f"Detected {len(mounts)} FUSE filesystems in total")
    
    return mounts

def _determine_fuse_type(mount_info):
    mount_info_lower = mount_info.lower()
    
    for fuse_type, keywords in FUSE_TYPES.items():
        for keyword in keywords:
            if keyword in mount_info_lower:
                return fuse_type
    
    return 'generic'

def detect_all_fuse_filesystems():
    return detect_fuse_filesystems()