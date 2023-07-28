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
    max_retries: int = 3,
    retry_delay_sec: int = 5,
) -> tuple[bool, str]:
    is_download_successful = False
    info = ""

    def progress_reporthook(n_blocks_transferred, block_size, file_tot_size):
        already_got_bytes = n_blocks_transferred * block_size
        if file_tot_size == -1:
            pass
        else:
            percent_p = int(100 * (already_got_bytes / file_tot_size))
            progress(percent_p)

    log.debug(f"Now downloading: {src_url}")

    for attempt in range(1, max_retries + 1):
        try:
            urllib.request.urlretrieve(
                src_url,
                filename=dest_path,
                reporthook=progress_reporthook,
            )
            log.debug("...done downloading.")
            is_download_successful = True
            info = ""
            return (is_download_successful, info)
        except Exception as error:
            log.error(f"Attempt {attempt} of {max_retries} failed")
            log.error(error)
            info = str(error)
            time.sleep(retry_delay_sec)
    is_download_successful = False
    info = "Failed to download file. " + info
    return (is_download_successful, info)
