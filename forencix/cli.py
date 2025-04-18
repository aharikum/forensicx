#!/usr/bin/env python3
"""
Command-line interface for ForensicX

Usage:
    forensicx --mount /path/to/fuse/mount

References:
- https://github.com/libfuse/libfuse
- https://www.sleuthkit.org/sleuthkit/
"""

import os
import sys
import argparse
import json
import datetime
from forensicx.fuse_detection import detect_all_fuse_filesystems
from forensicx.file_recovery import recover_deleted_files
from forensicx.metadata_extraction import extract_all_metadata
from forensicx.integrity_checker import generate_baseline, verify_integrity
from forensicx.utils import setup_logging, write_json_file

def main():
    
    parser = argparse.ArgumentParser(description='ForensicX: FUSE Filesystem Forensic Tool')
    parser.add_argument('--mount', required=True, help='FUSE mount point to analyze')
    parser.add_argument('--output-dir', default='forensicx_output',
                        help='Output directory for results')
   
    args = parser.parse_args()
    
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
    output_dir = args.output_dir
    
    # Setting up logging for the tool
    logger = setup_logging(os.path.join(output_dir, 'forensicx.log'))
    
    # Every tool needs a big flashy banner. Made in https://patorjk.com/software/taag/ 
    print("""
    ███████╗ ██████╗ ██████╗ ███████╗███╗   ██╗███████╗██╗ ██████╗██╗  ██╗
    ██╔════╝██╔═══██╗██╔══██╗██╔════╝████╗  ██║██╔════╝██║██╔════╝╚██╗██╔╝
    █████╗  ██║   ██║██████╔╝█████╗  ██╔██╗ ██║███████╗██║██║      ╚███╔╝ 
    ██╔══╝  ██║   ██║██╔══██╗██╔══╝  ██║╚██╗██║╚════██║██║██║      ██╔██╗ 
    ██║     ╚██████╔╝██║  ██║███████╗██║ ╚████║███████║██║╚██████╗██╔╝ ██╗
    ╚═╝      ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═══╝╚══════╝╚═╝ ╚═════╝╚═╝  ╚═╝
    FUSE Filesystem Forensic Tool
    """)
    
    logger.info("Starting ForensicX analysis")
    
    results = {
        'analysis_info': {
            'timestamp': datetime.datetime.now().isoformat(),
            'mount_point': args.mount,
            'output_directory': output_dir
        },
        'fuse_detection': None,
        'metadata': None,
        'integrity': None,
        'recovery': None
    }
    
    logger.info("Detecting FUSE filesystems")
    fuse_mounts = detect_all_fuse_filesystems()
    results['fuse_detection'] = fuse_mounts
    
    target_mount_info = None
    for mount in fuse_mounts:
        if mount['mount_point'] == args.mount:
            target_mount_info = mount
            break
    
    if not target_mount_info:
        logger.warning(f"Mount point {args.mount} not detected as FUSE filesystem. Analysis may be limited.")
        target_mount_info = {
            'mount_point': args.mount,
            'fuse_type': 'unknown'
        }
    
    logger.info(f"Extracting metadata from {args.mount}")
    metadata_file = os.path.join(output_dir, 'metadata.json')
    results['metadata'] = extract_all_metadata(args.mount, metadata_file)
    
    logger.info(f"Generating integrity baseline for {args.mount}")
    baseline_file = os.path.join(output_dir, 'baseline.json')
   # Check if baseline already exists
    if not os.path.isfile(baseline_file):
        # If no baseline exists, create one
        logger.info(f"Creating new integrity baseline")
        results['integrity'] = {
            'baseline': generate_baseline(args.mount, baseline_file)
        }
    else:
        # If baseline exists, load it 
        logger.info(f"Using existing integrity baseline")
        with open(baseline_file, 'r') as f:
            baseline_data = json.load(f)
        results['integrity'] = {
            'baseline': baseline_data
        }
            
        # Verify integrity against existing baseline
        logger.info(f"Verifying integrity against baseline")
        results['integrity']['verification'] = verify_integrity(args.mount, baseline_file)
        
        # Show the changes in file integrity
        if 'verification' in results['integrity']:
            verification = results['integrity']['verification']
            print(f"- Files Modified: {verification['summary']['modified_files']}")
            print(f"- Files Added: {verification['summary']['new_files']}")
            print(f"- Files Deleted: {verification['summary']['missing_files']}")
            
    logger.info(f"Attempting to recover deleted files from {args.mount}")
    recovery_dir = os.path.join(output_dir, 'recovered_files')
    if not os.path.exists(recovery_dir):
        os.makedirs(recovery_dir)
    results['recovery'] = recover_deleted_files(
        args.mount, 
        target_mount_info.get('fuse_type', 'generic'),
        recovery_dir
    )
    
    results_file = os.path.join(output_dir, 'forensicx_results.json')
    write_json_file(results_file, results)
    
    print("\nForensicX Analysis Summary:")
    print(f"- Mount Point: {args.mount}")
    print(f"- FUSE Type: {target_mount_info.get('fuse_type', 'unknown')}")
    print(f"- Metadata Extracted: {len(results['metadata'].get('files', {}))} files")
    print(f"- Baseline Generated: {len(results['integrity']['baseline'].get('files', {}))} files")
    
    recovery_results = results['recovery']
    recovered_count = len(recovery_results.get('recovered_files', []))
    print(f"- Files Recovered: {recovered_count}")
    
    if recovery_results.get('errors'):
        print(f"- Recovery Errors: {len(recovery_results.get('errors'))}")
    
    print(f"\nAll results saved to: {output_dir}")
    print(f"Full report: {results_file}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())