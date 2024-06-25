from typing import List
from typing import Optional


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
        copy_elf (bool, optional): _description_. Defaults to True.
        extra_files (Optional[List[str]], optional): _description_. Defaults to None.
    """
    raise NotImplementedError()
