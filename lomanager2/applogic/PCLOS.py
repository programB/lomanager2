"""
This module gathers functions to get or set operating system state.
Functions that use basic operations on the operating system either
to get information or to cause some changes in the operating system
and this by directly calling external, system program or by methods
from python standard library.
These are service providing functions, not procedures in app's logic.

These functions must not not hold any state (or be made to hold it
by turning them into closures or classes) - they should get the information
directly from the system on each call.
"""


import time
import os
import shutil
import pathlib
from typing import Callable
from configuration import logging as log
import urllib.request, urllib.error
import hashlib


def has_root_privileges() -> bool:
    return os.geteuid == 0


def run_shell_command(command: str, shell="bash", timeout=1) -> str:
    # TODO: Implement
    stdout_stderr = ""
    return stdout_stderr


def get_PID_by_name(names: list[str]) -> dict[str, str]:
    """Checks PIDs of any running processes passed by executable names."""
    # TODO: Implement
    pass


def get_running_package_managers() -> dict[str, str]:
    # TODO: Implement
    package_managers = {"fake_pacman": "9999", "fake_synaptic": "7777"}
    log.debug(f">>PRETENDING<< running package manager: {package_managers}")
    return package_managers


def get_running_Office_processes() -> dict[str, str]:
    binaries_to_check = ["soffice.bin"]
    # return get_PID_by_name(binaries_to_check)
    return {"soffice.bin": "3333"}


def get_system_users() -> list[str]:
    # TODO: Implement
    pass


def is_live_session_active() -> bool:
    # TODO: Verify implementation
    return pathlib.Path("/union").exists()


def get_system_update_status() -> tuple[bool, bool, str]:
    # TODO: Implement
    check_successful = True
    system_updated = False
    explanation = "System not updated"
    return (check_successful, system_updated, explanation)


def is_lomanager2_latest(lomanger2_version: str) -> bool:
    # TODO: Implement
    return True


def free_space_in_dir(dir: pathlib.Path) -> int:
    """Return free disk space for the partition holding dir.

    Returns
    -------
    free_space : int
        Free space in kibibytes (KiB).
    """

    free_space = int(shutil.disk_usage(dir).free / 1024)
    log.debug(f"free space in {dir}: {free_space} KiB")
    return free_space


def is_java_installed() -> bool:
    # TODO: Implement
    is_java_installed = False
    log.debug(f">>PRETENDING<< is_java_installed: {is_java_installed}")
    return is_java_installed


def detect_installed_java() -> tuple[bool, str]:
    # if pathlib.Path("/usr/bin/java").exists():
    #     java_version = ""
    #     found = True
    #     try:
    #         # get version
    #         pass
    #     except:
    #         # could not determine java version
    #         java_version = ""
    #         pass
    #     else:
    #         pass
    #     log.debug(f">>PRETENDING<< Found Java version: {java_version}")
    #     return (found, java_version)
    # return (False, "")
    # return(False, "")  # Test 1
    return(True, "")  # Test 2
    # return(True, "")  # Test 3
    # return(False, "")  # Test 4
    # return(False, "")  # Test 5
    # return(True, "")  # Test 6
    # return(True, "")  # Test 7


def detect_installed_office_software() -> list[tuple[str, str, tuple]]:
    # # Test 1
    # det_soft = []

    # Test 2
    det_soft = [
        (
            "LibreOffice",
            "7.4",
            (),
        ),
    ]

    # Test 3
    # det_soft = [
    #     (
    #         "LibreOffice",
    #         "7.4",
    #         (
    #             "pl",
    #             "fr",
    #         ),
    #     ),
    # ]

    # Test 4
    # det_soft = [
    #     ("OpenOffice", "2.0", ()),
    # ]

    # Test 5
    # det_soft = []

    # Test 6
    # det_soft = [
    #     (
    #         "LibreOffice",
    #         "7.5",
    #          (),
    #     ),
    # ]

    # Test 7
    # det_soft = [
    #     (
    #         "LibreOffice",
    #         "7.4",
    #         (
    #             "de",
    #         ),
    #     ),
    # ]

    # Test X
    # det_soft = [
    #     ("OpenOffice", "2.0", ()),
    #     (
    #         "OpenOffice",
    #         "2.4",
    #         (
    #             "pl",
    #             "gr",
    #         ),
    #     ),
    #     (
    #         "LibreOffice",
    #         "3.0.0",
    #         (
    #             "fr",
    #             "de",
    #         ),
    #     ),
    #     (
    #         "LibreOffice",
    #         "7.5",
    #         (
    #             "jp",
    #             "pl",
    #         ),
    #     ),
    # ]
    log.debug(f">>PRETENDING<< Found Office software: {det_soft}")
    return det_soft


def detect_installed_clipart() -> tuple[bool, str]:
    clipart_version = "5.3"
    found = True
    log.debug(f">>PRETENDING<< Found clipart library: {(found, clipart_version)}")
    return (found, clipart_version)


def download_file(
    src_url: str,
    dest_path: pathlib.Path,
    progress: Callable,
    progress_description: Callable,
    max_retries: int = 3,
    retry_delay_sec: int = 5,
) -> tuple[bool, str]:
    info = ""

    def progress_reporthook(n_blocks_transferred, block_size, file_tot_size):
        already_got_bytes = n_blocks_transferred * block_size
        if file_tot_size == -1:
            pass
        else:
            percent_p = int(100 * (already_got_bytes / file_tot_size))
            progress(percent_p)

    filename = src_url.split("/")[-1]
    progress_description(f"Now downloading: {filename}")

    for attempt in range(1, max_retries + 1):
        try:
            urllib.request.urlretrieve(
                src_url,
                filename=dest_path,
                reporthook=progress_reporthook,
            )
            progress_description(f"Downloaded:      {filename}")
            return (True, "")
        except Exception as error:
            log.error(f"Attempt {attempt} of {max_retries} failed")
            log.error(error)
            info = str(error)
            time.sleep(retry_delay_sec)
    info = "Failed to download file. " + info
    return (True, info)


def verify_checksum(
    file: pathlib.Path,
    checksum_file: pathlib.Path,
    progress: Callable,
    progress_description: Callable,
) -> bool:
    progress_description(f"Verifying:       {file.name}")

    with open(file, "rb") as f:
        file_tot_size = file.stat().st_size
        chunk_size = 8192
        steps = int(file_tot_size / chunk_size) + 2
        i = 0
        file_hash = hashlib.md5()
        while chunk := f.read(chunk_size):
            file_hash.update(chunk)
            progress_p = int((i / (steps)) * 100)
            progress(progress_p)
            i += 1

    calculated_hash = file_hash.hexdigest()

    with open(checksum_file, "r") as fmd:
        lines = fmd.readlines()
    checksum = lines[0].split()[0]  # first word in the first line

    if is_correct := calculated_hash == checksum:
        progress_description(f"hash OK:         {file.name}")
    return is_correct


def remove_file(path: pathlib.Path) -> bool:
    allowed_dirs = [
        pathlib.Path("/tmp"),
    ]
    path = path.expanduser()

    if not any(map(path.is_relative_to, allowed_dirs)):
        log.error(
            f"This program should not be trying to remove files from this "
            f"location! Refusing to remove: {path}"
        )
        is_removed = False
    else:
        try:
            os.remove(path)
            is_removed = True
        except Exception as error:
            msg = f"Error when removing {path}: "
            log.error(msg + str(error))
            is_removed = False
    return is_removed


def move_file(from_path: pathlib.Path, to_path: pathlib.Path) -> bool:
    try:
        shutil.move(src=from_path, dst=to_path)
        is_moved = True
    except Exception as error:
        msg = f"Error when moving {from_path} to {to_path}: "
        log.error(msg + str(error))
        is_moved = False
    return is_moved
