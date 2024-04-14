from pathlib import Path
from collections import namedtuple
from loguru import logger
import datetime
import time


DIRECTORY = Path("C:\\Users\\momoore\\OneDrive - Mazak Corporation\\Documents")
SORT_OPTIONS = ['total_files', 'files', 'subdirectories', 'recursive_files', 'folders']


Counts = namedtuple("Counts", ["subdirectories", "files", "recursive_files"])


def setup_logger() -> None:
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    logger.add(f"logs/{timestamp}.log", rotation="500 MB", level="DEBUG")


def get_directories(directory) -> list[Path]:
    start_time = time.perf_counter()
    directories = [d for d in directory.iterdir() if d.is_dir()]
    elapsed = time.perf_counter() - start_time
    logger.debug("Getting directories in: {} took {:.2f} seconds", directory, elapsed)
    return directories


def sort(iterable, key=None, reverse=False) -> list:
    start_time = time.perf_counter()
    sorted_list = sorted(iterable, key=key, reverse=reverse)
    elapsed = time.perf_counter() - start_time
    logger.debug("Sorting items took {:.2f} seconds", elapsed)
    return sorted_list


def count_files(directory: Path) -> int:
    start_time = time.perf_counter()
    count = len([f for f in directory.iterdir() if f.is_file()])
    elapsed = time.perf_counter() - start_time
    logger.debug("Counted {} files in {} took {:.2f} seconds", count, directory, elapsed)
    return count


def count_files_recursive(directory: Path, ignore: list = None) -> int:
    start_time = time.perf_counter()

    if ignore is None:
        ignore = []
    
    count = 0

    for file in directory.iterdir():
        if file.is_file():
            count += 1
        elif file.is_dir():
            if file.name in ignore:
                logger.warning("Ignoring directory: {}", file)
                continue
            else:
                count += count_files_recursive(file, ignore)

    elapsed = time.perf_counter() - start_time

    logger.debug("Recursive file count in {} is {}, took {:.2f} seconds", directory, count, elapsed)

    return count


def count_subdirectories(directory: Path) -> int:
    start_time = time.perf_counter()
    count = len([d for d in directory.iterdir() if d.is_dir()])
    elapsed = time.perf_counter() - start_time
    logger.debug("Counted {} subdirectories in {} took {:.2f} seconds", count, directory, elapsed)
    return count


def sort_directories(counts: dict, sort_by: str) -> list[Path]:
    if sort_by == "total_files" or sort == "recursive_files":
        return sort(counts, key=lambda dir: counts[dir].recursive_files, reverse=True)
    elif sort_by == "files":
        return sort(counts, key=lambda dir: counts[dir].files, reverse=True)
    elif sort_by == "subdirectories" or sort_by == "folders":
        return sort(counts, key=lambda dir: counts[dir].subdirectories, reverse=True)
    else:
        return counts


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
    counts = {}

    for directory in directories:
        logger.info("Analyzing {}", directory)
        subdirs_count = count_subdirectories(directory)
        files_count = count_files(directory)
        recursive_files_count = count_files_recursive(directory, ignore)
        counts[directory] = Counts(subdirectories=subdirs_count, files=files_count, recursive_files=recursive_files_count)

    sorted_directories = sort_directories(counts, sort_by)

    sorted_directories = sort(counts, key=lambda dir: counts[dir].recursive_files, reverse=True)
    logger.info("Sorting completed")

    for directory in sorted_directories:
        logger.info("{}: {} subdirectories, {} files, {} total files", directory, counts[directory].subdirectories, counts[directory].files, counts[directory].recursive_files)

    sum_files = sum(counts[directory].recursive_files for directory in sorted_directories)

    elapsed_total = time.perf_counter() - start_total
    logger.info("Directory analysis complete...")
    logger.info(f"Indexed in {sum_files} files in {elapsed_total:.3f} seconds")


if __name__ == "__main__":
    ignore = ['node_modules', '.git', 'venv', 'logs', '__pycache__', '.vscode', '.idea', '.venv', 'env']
    sort_by = "total_files"
    main(sort_by=sort_by, ignore=ignore)

