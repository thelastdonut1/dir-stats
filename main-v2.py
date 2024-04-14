from pathlib import Path
from collections import namedtuple
from loguru import logger
from multiprocessing import Pool
from dataclasses import dataclass
import os
import datetime
import time


DIRECTORY = Path("C:\\Users\\momoore\\OneDrive - Mazak Corporation\\Documents")
SORT_OPTIONS = ['total_files', 'files', 'subdirectories', 'recursive_files', 'folders']


@dataclass
class Directory:
    path: Path
    subdirectories: int = 0
    files: int = 0
    recursive_files: int = 0


def setup_logger() -> None:
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    logger.add(f"logs/{timestamp}.log", rotation="500 MB", level="DEBUG")


def get_directories(dir: Directory) -> None:
    start_time = time.perf_counter()
    directories = [Directory(path=d) for d in dir.iterdir() if d.is_dir()]
    elapsed = time.perf_counter() - start_time
    logger.debug("Getting directories in: {} took {:.2f} seconds", dir, elapsed)
    return directories


def sort(iterable, key=None, reverse=False) -> list:
    start_time = time.perf_counter()
    sorted_list = sorted(iterable, key=key, reverse=reverse)
    elapsed = time.perf_counter() - start_time
    logger.debug("Sorting items took {:.2f} seconds", elapsed)
    return sorted_list


def count_files(dir: Directory) -> None:
    start_time = time.perf_counter()
    count = len([f for f in dir.path.iterdir() if f.is_file()])
    elapsed = time.perf_counter() - start_time
    logger.debug("Counted {} files in {} took {:.2f} seconds", count, dir, elapsed)
    dir.files = count


def count_files_recursive_mp(args) -> int:
    dir, ignore = args
    count = 0
    try:
        for entry in os.scandir(dir.path):
            if entry.is_file():
                count += 1
            elif entry.is_dir() and entry.name not in ignore:
                subdir_count = count_files_recursive_mp((Directory(path=entry.path), ignore))
                count += subdir_count
    except PermissionError:
        logger.warning("Permission denied: {}", dir.path)
    return count


def count_subdirectories(dir: Directory) -> None:
    start_time = time.perf_counter()
    count = len([d for d in dir.path.iterdir() if d.is_dir()])
    elapsed = time.perf_counter() - start_time
    logger.debug("Counted {} subdirectories in {} took {:.2f} seconds", count, dir, elapsed)
    dir.subdirectories = count


def sort_directories(directories: list[Directory], sort_by: str) -> list[Directory]:
    if sort_by == "total_files" or sort == "recursive_files":
        return sort(directories, key=lambda dir: dir.recursive_files, reverse=True)
    elif sort_by == "files":
        return sort(directories, key=lambda dir: dir.files, reverse=True)
    elif sort_by == "subdirectories" or sort_by == "folders":
        return sort(directories, key=lambda dir: dir.subdirectories, reverse=True)
    else:
        return directories


def main(sort_by: str = None, ignore: list = None) -> None:
    setup_logger()

    if ignore is None:
        ignore = []  # Avoid mutable default arguments

    if sort_by is None:
        sort_by = "total_files"

    if sort_by not in SORT_OPTIONS:
        logger.error("Invalid sort option: {}", sort_by)
        return

    logger.info("Starting directory analysis")
    start_total = time.perf_counter()
    assert DIRECTORY.exists(), f"{DIRECTORY} does not exist"
    logger.info("{} exists, proceeding with directory analysis", DIRECTORY)

    directories = get_directories(DIRECTORY)

    with Pool(processes=os.cpu_count()) as pool:
        # Create tasks for each directory
        tasks = [(directory, ignore) for directory in directories]
        # Process directories in parallel
        results = pool.map(count_files_recursive_mp, tasks)

    for directory, result in zip(directories, results):
        directory.recursive_files = result
        count_files(directory)
        count_subdirectories(directory)

    sorted_directories = sort_directories(directories, sort_by)

    logger.info("Sorting completed")

    for directory in sorted_directories:
        logger.info(f"{directory.path}: {directory.subdirectories} subdirectories, {directory.files} files, {directory.recursive_files} total files")

    sum_files = sum(directory.recursive_files for directory in sorted_directories)

    elapsed_total = time.perf_counter() - start_total
    logger.info("Directory analysis complete...")
    logger.info(f"Indexed in {sum_files} files in {elapsed_total:.3f} seconds")


if __name__ == "__main__":
    ignore = []
    # ignore = ['node_modules', '.git', 'venv', 'logs', '__pycache__', '.vscode', '.idea', '.venv', 'env']
    sort_by = "total_files"
    main(sort_by=sort_by, ignore=ignore)

