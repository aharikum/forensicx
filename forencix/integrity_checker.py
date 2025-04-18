#!/usr/bin/env python3
"""
File Integrity Checker Module for FUSE filesystems

References:
- https://docs.python.org/3/library/hashlib.html
- https://en.wikipedia.org/wiki/File_verification
"""

import os
import hashlib
import json
import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)

DEFAULT_HASH_ALGORITHMS = ['md5', 'sha256']

def calculate_file_hashes(file_path, algorithms=None):
    """
    Calculate hashes for a file using specified algorithms
    """
    if algorithms is None:
        algorithms = DEFAULT_HASH_ALGORITHMS
    
    hashes = {}
    
    try:
        # Initialize hash objects
        hash_objects = {}
        for algorithm in algorithms:
            if algorithm == 'md5':
                hash_objects[algorithm] = hashlib.md5()
            elif algorithm == 'sha1':
                hash_objects[algorithm] = hashlib.sha1()
            elif algorithm == 'sha256':
                hash_objects[algorithm] = hashlib.sha256()
            elif algorithm == 'sha512':
                hash_objects[algorithm] = hashlib.sha512()
            else:
                logger.warning(f"Unsupported hash algorithm: {algorithm}")
        
        # Read file in chunks to handle large files
        with open(file_path, 'rb') as f:
            while True:
                data = f.read()
                if not data:
                    break
                for hash_obj in hash_objects.values():
                    hash_obj.update(data)

    except Exception as e:
        logger.error(f"Error calculating hashes for {file_path}: {e}")
        hashes['error'] = str(e)
    
    return hashes

def generate_baseline(mount_point, output_file=None):
    """
    Generate baseline hashes for all files in the filesystem
    """
    logger.info(f"Generating baseline for {mount_point}")
    
    baseline = {
        'timestamp': datetime.now().isoformat(),
        'mount_point': mount_point,
        'files': {},
        'errors': []
    }
    
    try:
        # Walk the filesystem
        for root, _, files in os.walk(mount_point):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                rel_path = os.path.relpath(file_path, mount_point)
                
                try:
                    # Generate hashes
                    hashes = calculate_file_hashes(file_path)
                    file_stat = os.stat(file_path)
                    
                    baseline['files'][rel_path] = {
                        'hashes': hashes,
                        'size': file_stat.st_size,
                        'mtime': datetime.fromtimestamp(file_stat.st_mtime).isoformat()
                    }
                except Exception as e:
                    error_msg = f"Error processing {rel_path}: {str(e)}"
                    logger.error(error_msg)
                    baseline['errors'].append(error_msg)
    
    except Exception as e:
        error_msg = f"Error walking filesystem {mount_point}: {str(e)}"
        logger.error(error_msg)
        baseline['errors'].append(error_msg)
    
    # Save to file if requested
    if output_file:
        try:
            with open(output_file, 'w') as f:
                json.dump(baseline, f, indent=2)
            logger.info(f"Baseline saved to {output_file}")
        except Exception as e:
            error_msg = f"Error saving baseline to {output_file}: {str(e)}"
            logger.error(error_msg)
            baseline['errors'].append(error_msg)
    
    return baseline

def verify_integrity(mount_point, baseline_file=None):
    """
    Verify file integrity against a previous baseline
    """
    logger.info(f"Verifying integrity of {mount_point}")
    
    if baseline_file is None:
        baseline_file = os.path.join('forensicx_output', 'baseline.json')
    
    verification_results = {
        'timestamp': datetime.now().isoformat(),
        'mount_point': mount_point,
        'baseline_file': baseline_file,
        'files': {
            'unchanged': [],
            'modified': [],
            'new': [],
            'missing': []
        },
        'summary': {
            'total_files': 0,
            'unchanged_files': 0,
            'modified_files': 0,
            'new_files': 0,
            'missing_files': 0
        },
        'errors': []
    }
    
    # previous baseline is passed on to through argument.
    # reusing generate_baseline to get the hashes for current files
    current_baseline = generate_baseline(mount_point)
    current_files = current_baseline.get('files', {})
    
    if not os.path.exists(baseline_file):
        verification_results['errors'].append(f"Previous baseline file not found: {baseline_file}")
        verification_results['summary']['new_files'] = len(current_files)
        verification_results['summary']['total_files'] = len(current_files)
        verification_results['files']['new'] = list(current_files.keys())
        return verification_results
    
    try:
        # Load previous baseline
        with open(baseline_file, 'r') as f:
            previous_baseline = json.load(f)
        
        previous_files = previous_baseline.get('files', {})
        
        # Compare files
        current_paths = set(current_files.keys())
        previous_paths = set(previous_files.keys())
        
        # Trying to find unchanged or any modified files from the 
        # intersection of previous baseline report and new report
        for path in current_paths.intersection(previous_paths):
            current_info = current_files[path]
            previous_info = previous_files[path]

            current_hashes = current_info.get('hashes', {})
            previous_hashes = previous_info.get('hashes', {})
            
            if (current_hashes.get('md5') == previous_hashes.get('md5') and
                current_hashes.get('sha256') == previous_hashes.get('sha256')):
                verification_results['files']['unchanged'].append(path)
                verification_results['summary']['unchanged_files'] += 1
            else:
                # Hashes don't match.. file was modified, we'll report that.
                modification = {
                    'path': path,
                    'previous': previous_info,
                    'current': current_info,
                    'changes': []
                }
                
                # Identify the change in size
                if current_info.get('size') != previous_info.get('size'):
                    modification['changes'].append('size')
                
                for algo in ['md5', 'sha256']:
                    if (algo in previous_hashes and algo in current_hashes and
                        previous_hashes[algo] != current_hashes[algo]):
                        modification['changes'].append(algo)
                
                verification_results['files']['modified'].append(modification)
                verification_results['summary']['modified_files'] += 1
        
        # Check for any new files?
        for path in current_paths - previous_paths:
            verification_results['files']['new'].append({
                'path': path,
                'info': current_files[path]
            })
            verification_results['summary']['new_files'] += 1
        
        # Check for any deleted files?
        for path in previous_paths - current_paths:
            verification_results['files']['missing'].append({
                'path': path,
                'info': previous_files[path]
            })
            verification_results['summary']['missing_files'] += 1
        
        # Tally all the files
        verification_results['summary']['total_files'] = (
            verification_results['summary']['unchanged_files'] +
            verification_results['summary']['modified_files'] +
            verification_results['summary']['new_files'] +
            verification_results['summary']['missing_files']
        )
    
    except Exception as e:
        error_msg = f"Error during verification: {str(e)}"
        logger.error(error_msg)
        verification_results['errors'].append(error_msg)
    
    return verification_results