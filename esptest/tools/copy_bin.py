import argparse
import logging
import shutil
from pathlib import Path
from typing import List, Optional

try:
    # Run from `python -m esptest.tools.set_att`
    from ..logger import get_logger
except ImportError:
    from esptest.logger import get_logger

logger = get_logger('copy_bin')


class BuildFilesPatterns:
    BIN_FILES = [
        '*.bin',
        'bootloader/*.bin',
        'partition_table/*.bin',
        'flasher_args.json',
        'flash_project_args',
        'config/sdkconfig.json',
        'sdkconfig',
    ]
    # For extra debugging
    MAP_AND_ELF_FILES = [
        'project_description.json',
        'bootloader/*.map',
        'bootloader/*.elf',
        '*.map',
        '*.elf',
    ]


def copy_bin_to_new_path(
    from_dir: str,
    to_dir: str,
    force: bool = True,
    copy_elf: bool = True,
    extra_files: Optional[List[str]] = None,
) -> None:
    """Copy build files to new path

    Args:
        from_dir (str): the app build directory. eg: ./build/
        to_dir (str): Destination directory to save the bin files.
        force (bool, optional): Delete the destination dir if it is already exists. Defaults to True.
        copy_elf (bool, optional): Copy elf and map files as well. Defaults to True.
        extra_files (Optional[List[str]], optional): . Defaults to None.
    """
    from_path = Path(from_dir).resolve().absolute()
    to_path = Path(to_dir).resolve().absolute()
    logger.debug(f'Copying bin files from {from_path} to {to_path}')
    assert from_path.is_dir()
    if force and to_path.is_dir():
        logger.debug(f'Removing existing destination directory {to_path}')
        shutil.rmtree(str(to_path))
    assert not to_path.exists()
    to_path.mkdir(parents=True)

    all_patterns = BuildFilesPatterns.BIN_FILES
    if copy_elf:
        all_patterns.extend(BuildFilesPatterns.MAP_AND_ELF_FILES)
    if extra_files:
        all_patterns.extend(extra_files)

    for pattern in BuildFilesPatterns.BIN_FILES:
        for _file in from_path.glob(pattern):
            assert _file.is_file()
            relative_path = _file.relative_to(from_path)
            to_file = to_path / relative_path
            if not to_file.parent.is_dir():
                to_file.parent.mkdir(parents=True)
            logging.debug(f'Copying file {relative_path}')
            shutil.copy(_file, to_path / relative_path)


def main() -> None:
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser(description='Copy bin files')
    parser.add_argument('from_dir', type=str, help='source directory of build bin files')
    parser.add_argument('to_dir', type=str, help='destination directory')
    args = parser.parse_args()

    copy_bin_to_new_path(args.from_dir, args.to_dir)


if __name__ == '__main__':
    main()
