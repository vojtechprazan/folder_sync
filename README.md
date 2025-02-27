# Directory Synchronization Script

## Overview

This script synchronizes the contents of a source directory with a replica directory. It ensures that all files from the source are copied to the replica, and any files not present in the source are removed from the replica. The script runs periodically, as specified by the user.

## Script Description

### Usage

The script is intended to be run from the command line with the following arguments:
- `-s`, `--source`: The source directory to synchronize from (required).
- `-r`, `--replica`: The replica directory to synchronize to (required).
- `-l`, `--log`: Log file to store logs (required).
- `-p`, `--period`: The synchronization period in seconds (required).

### Example

```sh
python sync_directories.py -s /path/to/source -r /path/to/replica -l /path/to/log -p 60
```

### Limitations
Empty folders are deleted from replica folder and kept in source folder.

Tested only on Windows, might not work in other platforms.
