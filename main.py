import hashlib
import argparse
import os
import shutil
import time
import datetime

# Setting up argument parser
parser = argparse.ArgumentParser()
parser.add_argument('-s', '--source', required=True, help="source directory")
parser.add_argument('-r', '--replica', required=True, help="replica directory")
parser.add_argument('-l', '--log', required=True, help="log file")
parser.add_argument('-p', '--period', type=int, required=True, help="backup period")
args = parser.parse_args()

LOG_FILE = args.log


class FileNameHash:
    """Class to compute and store file hash and related path information."""

    BUF_SIZE = 65536

    def __init__(self, absolute_path, folder):
        """
        Initializes FileNameHash object with file path and folder information.

        Args:
            absolute_path (str): Absolute path of the file.
            folder (str): Base folder for relative path computation.
        """
        self.absolute_path = absolute_path
        self.path_relative_to_folder = get_file_path_relative_to_folder(self.absolute_path, folder)
        self.file_name = os.path.split(self.absolute_path)[-1]
        self.relative_file_name_to_folder = self.path_relative_to_folder + self.file_name
        self.hash_value = self._hash_file()

    def _hash_file(self):
        """Computes the MD5 hash of the file."""
        md5 = hashlib.md5()
        with open(self.absolute_path, 'rb') as f:
            while True:
                data = f.read(self.BUF_SIZE)
                if not data:
                    break
                md5.update(data)
            return md5.hexdigest()

    def __str__(self):
        return f"{self.absolute_path}"


def get_files_from_folder(folder):
    """
    Retrieves all files from a given folder and computes their hashes.

    Args:
        folder (str): Path to the folder.

    Returns:
        list: List of FileNameHash objects.
    """
    aggregate_files = [os.path.join(root, f) for root, _, files in os.walk(folder) for f in files]
    hashed_files = [FileNameHash(file, folder) for file in aggregate_files]
    return hashed_files


def get_file_path_relative_to_folder(file, folder):
    """
    Computes the relative path of a file with respect to a folder.

    Args:
        file (str): Absolute file path.
        folder (str): Base folder path.

    Returns:
        str: Relative path from the folder to the file.
    """
    split_file = os.path.split(file)
    relative_path = file[len(folder):-len(split_file[1])]
    return relative_path


def copy_file(item, replica_folder):
    """
    Copies a file to the replica folder, preserving directory structure.

    Args:
        item (FileNameHash): File to be copied.
        replica_folder (str): Path to the replica folder.
    """
    try:
        rel_path = item.path_relative_to_folder
        full_path = replica_folder + rel_path
        os.makedirs(full_path, exist_ok=True)
        shutil.copy(item.absolute_path, full_path)
        message = f"{datetime.datetime.now()} copied: {item}"
        log_message(message)
    except Exception as e:
        message = f"Exception {e} caught during copying file {item}"
        log_message(message)


def remove_file(files_to_remove):
    """
    Removes specified files.

    Args:
        files_to_remove (list): List of FileNameHash objects to be removed.
    """
    try:
        for item in files_to_remove:
            os.remove(item.absolute_path)
            message = f"{datetime.datetime.now()} removed: {item}"
            log_message(message)
    except Exception as e:
        message = f"Exception {e} caught during removing file {item}"
        log_message(message)


def remove_empty_dirs(dir_name):
    """
    Removes empty directories within the specified directory.

    Args:
        dir_name (str): Path to the directory.
    """
    empty_dirs = [dirpath for dirpath, _, _ in os.walk(dir_name) if len(os.listdir(dirpath)) == 0]
    try:
        for item in empty_dirs:
            os.rmdir(item)
            message = f"{datetime.datetime.now()} removed empty dir: {item}"
            log_message(message)
    except Exception as e:
        message = f"Exception {e} caught during removing empty dir {item}"
        log_message(message)


def log_message(message):
    """
    Logs a message to the log file and prints it.

    Args:
        message (str): Message to log.
    """
    with open(LOG_FILE, 'a') as f:
        f.write(message + '\n')
        print(message)


def synchronize_folder(source, replica):
    """
    Synchronizes the contents of the source folder with the replica folder.

    Args:
        source (str): Path to the source folder.
        replica (str): Path to the replica folder.
    """
    list_of_source_files = get_files_from_folder(source)
    list_of_replica_files = get_files_from_folder(replica)
    source_hash_values = [item.hash_value for item in list_of_source_files]
    replica_hash_values = [item.hash_value for item in list_of_replica_files]
    replica_file_names = [item.relative_file_name_to_folder for item in list_of_replica_files]

    # Copy new or updated files to replica
    for item in list_of_source_files:
        if item.relative_file_name_to_folder not in replica_file_names:
            copy_file(item, replica)
            continue

        if item.hash_value not in replica_hash_values:
            copy_file(item, replica)
            continue

    # Refresh file lists and hash values
    list_of_replica_files = get_files_from_folder(replica)
    new_replica_hash_values = [item for item in list_of_replica_files if item.hash_value not in source_hash_values]
    remove_file(new_replica_hash_values)

    list_of_replica_files = get_files_from_folder(replica)
    list_of_source_files = get_files_from_folder(source)
    source_file_names = [item.relative_file_name_to_folder for item in list_of_source_files]
    new_replica_names = [item for item in list_of_replica_files if item.relative_file_name_to_folder not in source_file_names]
    remove_file(new_replica_names)

    remove_empty_dirs(replica)


def main(source, replica, period):
    """
    Main function to synchronize the folders periodically.

    Args:
        source (str): Path to the source folder.
        replica (str): Path to the replica folder.
        period (int): Time interval between synchronizations in seconds.
    """
    while True:
        synchronize_folder(source, replica)
        time.sleep(int(period))


if __name__ == "__main__":
    if not os.path.isdir(args.source):
        log_message(f"Source directory '{args.source}' does not exist.")
        exit(1)

    if not os.path.isdir(args.replica):
        log_message(f"Replica directory '{args.source}' does not exist.")
        exit(1)

    main(args.source, args.replica, args.period)

