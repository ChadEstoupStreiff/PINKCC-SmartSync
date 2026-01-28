import argparse
import logging
import os
import shutil
import time
from datetime import datetime

from tqdm import tqdm


def walk_folder(folder, ignore_files=None, ignore_extensions=None, ignore_hidden=True):
    """
    Walks through a folder and returns a list of all relatives file paths within it.

    Args:
        folder (str): Path to the folder.
        ignore_files (list): List of file paths or folders to ignore.
        ignore_extensions (list): List of file extensions to ignore.
        ignore_hidden (bool): If True, ignores hidden files and folders.
    Returns:
        list: List of file paths.
    """
    file_paths = []
    ignore_files = ignore_files or []
    ignore_extensions = ignore_extensions or []

    for root, dirs, files in os.walk(folder):
        
        for d in dirs[::-1]:
            rel_dir_path = os.path.relpath(os.path.join(root, d), folder)
            
            if ignore_hidden and d.startswith("."):
                dirs.remove(d)
                continue
                
            if any(rel_dir_path == ign or rel_dir_path.startswith(os.path.join(ign, "")) for ign in ignore_files):
                dirs.remove(d)
                continue

        for file in files:
            if ignore_hidden and file.startswith("."):
                continue
                
            relative_path = os.path.relpath(os.path.join(root, file), folder)

            if any(relative_path == ign for ign in ignore_files):
                continue

            if any(relative_path.endswith(ext) for ext in ignore_extensions):
                continue

            file_paths.append(relative_path)

    return file_paths


def sync_folders(
    folderA,
    folderB,
    sync_most_recent=False,
    ignore_files=None,
    ignore_extensions=None,
    ignore_hidden=True,
):
    """
    Syncs files between two folders, ensuring both folders have the same files.
    If a file exists in one folder but not the other, it is copied over.

    Args:
        folderA (str): Path to the first folder.
        folderB (str): Path to the second folder.
        sync_most_recent (bool): If True, syncs the most recently modified files.
        ignore_filess (list): Paths to files or folders containing list of files to ignore during sync.
        ignore_extensions (list): List of file extensions to ignore during sync.
        ignore_hidden (bool): If True, ignores hidden files and folders during sync.
    Returns:
        list: List of synced file paths.
    """
    folderA_files = walk_folder(folderA, ignore_files, ignore_extensions, ignore_hidden)
    folderB_files = walk_folder(folderB, ignore_files, ignore_extensions, ignore_hidden)

    def loop_files(files, rootA, rootB):
        """
        Loops through files and syncs them from rootA to rootB.
        Args:
            files (list): List of file paths to sync.
            rootA (str): Source folder path.
            rootB (str): Target folder path.
        Returns:
            list: List of synced file paths. (file, status).
        """
        as_been_synced = []
        for file in tqdm(
            files,
            desc=f"Syncing from {rootA} to {rootB}, total={len(files)}",
            unit="files",
        ):
            file_path = os.path.join(rootA, file)
            target_path = os.path.join(rootB, file)

            if not os.path.exists(target_path):
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                shutil.copy2(file_path, target_path)
                as_been_synced.append((file, "new"))
            elif sync_most_recent:
                if os.path.getmtime(file_path) > os.path.getmtime(target_path):
                    shutil.copy2(file_path, target_path)
                    as_been_synced.append((file, "more recent"))
        return as_been_synced

    start = time.time()
    synced_A_to_B = loop_files(folderA_files, folderA, folderB)  # Sync from A to B
    synced_B_to_A = loop_files(folderB_files, folderB, folderA)  # Sync from B to A

    full_time = time.time() - start
    logging.info(f"Sync completed in {time.time() - start} :) Saving logs...")

    log_filename = datetime.now().strftime("%Y-%m-%d_%H:%M:%S") + "_sync.log"
    if not os.path.exists(os.path.join(folderA, ".sync_logs")):
        os.makedirs(os.path.join(folderA, ".sync_logs"))
    if not os.path.exists(os.path.join(folderB, ".sync_logs")):
        os.makedirs(os.path.join(folderB, ".sync_logs"))

    with open(os.path.join(folderA, ".sync_logs", log_filename), "w") as log_file:
        log_file.write("Parameters:\n")
        log_file.write(f"  folderA: {folderA}\n")
        log_file.write(f"  folderB: {folderB}\n")
        log_file.write(f"  sync_most_recent: {sync_most_recent}\n")
        log_file.write(f"  ignore_files: {ignore_files}\n")
        log_file.write(f"  ignore_extensions: {ignore_extensions}\n\n")
        log_file.write(
            f"Synced {len(folderA_files) + len(folderB_files)} files ({len(synced_A_to_B) + len(synced_B_to_A)} copied) between {folderA} and {folderB} in {full_time} seconds.\n"
        )
        for file, status in synced_A_to_B:
            log_file.write(
                f"Because of '{status}': {os.path.join(folderA, file)} ==> {os.path.join(folderB, file)}\n"
            )
    with open(os.path.join(folderA, ".sync_logs", log_filename), "r") as log_file:
        logging.info(f"Sync Logs at {log_filename}:")
        logging.info(log_file.read())

    shutil.copy2(
        os.path.join(folderA, ".sync_logs", log_filename),
        os.path.join(folderB, ".sync_logs", log_filename),
    )

    logging.info(
        f"Logs saved to {os.path.join(folderA, '.sync_logs', log_filename)} and {os.path.join(folderB, '.sync_logs', log_filename)}."
    )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    parser = argparse.ArgumentParser()

    parser.add_argument("A", type=str, help="Path to the first folder.")
    parser.add_argument("B", type=str, help="Path to the second folder.")
    parser.add_argument(
        "--sync_most_recent",
        action="store_true",
        default=False,
        help="Sync the most recently modified files.",
    )
    parser.add_argument(
        "--ignore_files",
        type=str,
        nargs="*",
        default=None,
        help="List of file paths to ignore during sync.",
    )
    parser.add_argument(
        "--ignore_extensions",
        type=str,
        nargs="*",
        default=None,
        help="List of file extensions to ignore during sync.",
    )
    parser.add_argument(
        "--ignore_hidden",
        action="store_true",
        default=True,
        help="Ignore hidden files and folders during sync.",
    )

    args = parser.parse_args()
    if os.path.exists(args.A) is False:
        logging.error(f"Folder A does not exist: {args.A}")
        exit(1)
    if os.path.exists(args.B) is False:
        logging.error(f"Folder B does not exist: {args.B}")
        exit(1)

    sync_most_recent = args.sync_most_recent
    ignore_files = (
        args.ignore_files + [".sync_logs/"] if args.ignore_files else [".sync_logs/"]
    )
    ignore_extensions = args.ignore_extensions
    ignore_hidden = args.ignore_hidden

    logging.info(f"Starting sync between {args.A} and {args.B} with parameters:\n")
    logging.info(f"  sync_most_recent: {sync_most_recent}")
    logging.info(f"  ignore_files: {ignore_files}")
    logging.info(f"  ignore_extensions: {ignore_extensions}")
    logging.info(f"  ignore_hidden: {ignore_hidden}")

    sync_folders(
        args.A,
        args.B,
        sync_most_recent=sync_most_recent,
        ignore_files=ignore_files,
        ignore_extensions=ignore_extensions,
        ignore_hidden=ignore_hidden,
    )
