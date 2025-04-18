#!/usr/bin/env python3
"""
Metadata Extraction Module for FUSE filesystems

References:
- https://linux.die.net/man/2/stat
- https://github.com/libfuse/libfuse/wiki/Mount-options
"""

import os
import stat
import json
import logging
import pwd
import grp
from datetime import datetime

logger = logging.getLogger(__name__)

# got this from man page of stat
def get_file_type(mode):
    if stat.S_ISREG(mode):
        return "regular file"
    elif stat.S_ISDIR(mode):
        return "directory"
    elif stat.S_ISCHR(mode):
        return "character device"
    elif stat.S_ISBLK(mode):
        return "block device"
    elif stat.S_ISFIFO(mode):
        return "FIFO (named pipe)"
    elif stat.S_ISLNK(mode):
        return "symbolic link"
    elif stat.S_ISSOCK(mode):
        return "socket"
    else:
        return "unknown"

def extract_file_metadata(file_path):
    """
    Extract metadata from a single file
    """
    metadata = {}
    
    try:
        file_stat = os.stat(file_path, follow_symlinks=False)
        metadata['size'] = file_stat.st_size
        metadata['inode'] = file_stat.st_ino
        metadata['permissions'] = {
            'mode': file_stat.st_mode,
            'readable': os.access(file_path, os.R_OK),
            'writable': os.access(file_path, os.W_OK),
            'executable': os.access(file_path, os.X_OK)
        }
        metadata['type'] = get_file_type(file_stat.st_mode)
        metadata['ownership'] = {
            'uid': file_stat.st_uid,
            'gid': file_stat.st_gid
        }
        
        # https://docs.python.org/3/library/pwd.html 
        try:
            metadata['ownership']['user'] = pwd.getpwuid(file_stat.st_uid).pw_name
        except (ImportError, KeyError):
            pass
        
        # https://www.geeksforgeeks.org/grp-module-in-python/ 
        try:
            metadata['ownership']['group'] = grp.getgrgid(file_stat.st_gid).gr_name
        except (ImportError, KeyError):
            pass
        
        metadata['timestamps'] = {
            'access_time': datetime.fromtimestamp(file_stat.st_atime).isoformat(),
            'modification_time': datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
            'creation_time': datetime.fromtimestamp(file_stat.st_ctime).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error extracting metadata for {file_path}: {e}")
        metadata['error'] = str(e)
    
    return metadata

def get_filesystem_info(mount_point):
    fs_info = {
        'mount_point': mount_point
    }
    
    try:
        # To get the filesystem details based on calculations
        # reference : https://www.ibm.com/docs/en/zos/2.4.0?topic=functions-statvfs-get-file-system-information 
        fs_stat = os.statvfs(mount_point)
        block_size = fs_stat.f_frsize
        fs_info['statistics'] = {
            'total_space': block_size * fs_stat.f_blocks,
            'free_space': block_size * fs_stat.f_bfree,
            'available_space': block_size * fs_stat.f_bavail,
            'total_inodes': fs_stat.f_files,
            'free_inodes': fs_stat.f_ffree
        }
    
    except Exception as e:
        logger.error(f"Error getting filesystem info for {mount_point}: {e}")
        fs_info['error'] = str(e)
    
    return fs_info

def extract_all_metadata(mount_point, output_file=None):
    """
    Extract metadata from all files in the filesystem
    """
    logger.info(f"Extracting metadata from {mount_point}")
    
    metadata_results = {
        'filesystem_info': get_filesystem_info(mount_point),
        'files': {},
        'errors': []
    }
    
    try:
        # start with the filesystem mount_point
        for root, dirs, files in os.walk(mount_point):
            # Go through directories
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                rel_path = os.path.relpath(dir_path, mount_point)
                
                try:
                    dir_metadata = extract_file_metadata(dir_path)
                    metadata_results['files'][rel_path] = dir_metadata
                except Exception as e:
                    error_msg = f"Error extracting metadata for {rel_path}: {str(e)}"
                    logger.error(error_msg)
                    metadata_results['errors'].append(error_msg)
            
            # Go through and each file and process metadata
            for file_name in files:
                file_path = os.path.join(root, file_name)
                rel_path = os.path.relpath(file_path, mount_point)
                
                try:
                    file_metadata = extract_file_metadata(file_path)
                    metadata_results['files'][rel_path] = file_metadata
                except Exception as e:
                    error_msg = f"Error extracting metadata for {rel_path}: {str(e)}"
                    logger.error(error_msg)
                    metadata_results['errors'].append(error_msg)
    
    except Exception as e:
        error_msg = f"Error walking filesystem {mount_point}: {str(e)}"
        logger.error(error_msg)
        metadata_results['errors'].append(error_msg)
    
    if output_file:
        try:
            with open(output_file, 'w') as f:
                json.dump(metadata_results, f, indent=2)
            logger.info(f"Metadata saved to {output_file}")
        except Exception as e:
            error_msg = f"Error saving metadata to {output_file}: {str(e)}"
            logger.error(error_msg)
            metadata_results['errors'].append(error_msg)
    
    return metadata_results