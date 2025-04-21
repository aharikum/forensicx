#!/usr/bin/env python3
"""
File Recovery Module for FUSE filesystems

References:
- https://www.sleuthkit.org/sleuthkit/man/fls.html
- https://www.sleuthkit.org/sleuthkit/man/icat.html
- https://github.com/sleuthkit/sleuthkit
"""

import os
import re
import subprocess
import logging

logger = logging.getLogger(__name__)

SLEUTHKIT_TOOLS = ['fls', 'icat']

def recover_deleted_files(mount_point, fuse_type, output_dir):
    recovery_results = {
        'recovered_files': [],
        'errors': []
    }
    
    recovery_dir = os.path.join(output_dir, f"recovered_{os.path.basename(mount_point)}")
    os.makedirs(recovery_dir, exist_ok=True)
    
    try:
        logger.info(f"Running fls on {mount_point}")
        fls_result = subprocess.run(
            ['fls', '-rd', mount_point], 
            capture_output=True, 
            text=True
        )
        
        if fls_result.returncode != 0:
            error_msg = f"fls failed: {fls_result.stderr}"
            logger.error(error_msg)
            recovery_results['errors'].append(error_msg)
            return recovery_results
        
        # Process fls output
        for line in fls_result.stdout.splitlines():
            # Look for deleted files (marked with * or r/r)
            # fls marks deleted files with either an asterisk (*) or "r/r *" prefix
            # Format examples from fls output:
            #   r/r * 14:   file2.txt (deleted)
            #   r/r * 17-128-1:   document.pdf (deleted)
            # The regex looks for inode numbers which may include fragment info (e.g., 17-128-1)
            if '*' in line or 'r/r' in line:
                match = re.search(r'(\d+)[-:]', line)
                if match:
                    inode = match.group(1)
                    file_name = line.split(':', 1)[1].strip() if ':' in line else f"unknown_file_{inode}"
                    
                    output_file = os.path.join(recovery_dir, file_name)
                    
                    logger.info(f"Recovering inode {inode} to {output_file}")
                    
                    # Using icat to try and extract the file that is deleted
                    with open(output_file, 'wb') as f:
                        icat_result = subprocess.run(
                            ['icat', mount_point, inode], 
                            stdout=f,
                            stderr=subprocess.PIPE
                        )
                    
                    recovery_info = {
                        'inode': inode,
                        'filename': file_name,
                        'output_path': output_file,
                    }
                    
                    if icat_result.returncode != 0:
                        recovery_info['error'] = icat_result.stderr.decode('utf-8', errors='ignore')
                    else:
                        recovery_info['size'] = os.path.getsize(output_file)
                    
                    recovery_results['recovered_files'].append(recovery_info)
    
    except Exception as e:
        error_msg = f"Recovery failed: {str(e)}"
        logger.error(error_msg)
        recovery_results['errors'].append(error_msg)
    
    return recovery_results