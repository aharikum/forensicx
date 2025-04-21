# FORENSICX


ForensicX is a comprehensive forensic analysis tool designed specifically for FUSE (Filesystem in Userspace) based file systems. It enables investigators to recover files, extract metadata, and detect tampering within FUSE implementations such as encfs and bindfs.

## Features 
- **FUSE Filesystem Detection**: Automatically identifies mounted FUSE filesystems
- **File Recovery**: Recovers deleted files from FUSE-based storage. **Does not work.. explained below**
- **Metadata Extraction**: Extracts timestamps, ownership details, and permissions
- **Integrity Verification**: Implements SHA-256 and MD5 hashing to check file integrity
- **Tampering Detection**: Identifies unauthorized modifications or hidden files

## Prerequisites

- Python 3.8+
- The Sleuth Kit (provides fls, icat, and other forensic tools)
- FUSE and related filesystem implementations (encfs, bindfs, etc.)

## Installation

### Step 1: Install Dependencies

```bash
sudo apt-get update
sudo apt-get install -y sleuthkit fuse encfs bindfs
```

### Step 2: Setup Python environment and Install Forensicx tool

```bash
git clone https://github.com/aharikum/forensicx 
cd forensicx
python3 -m venv forensicx-env
source forensicx-env/bin/activate
pip install -e .
```

### Usage
To use the tool, run the following command
```bash
# For identifying the options available
forensicx --help

# Run the tool 
forensicx --mount <path_to_mount>
```

[^1]: This is footnote 1

---
**Created By** Akhil, Inzamam and Shrawani
---