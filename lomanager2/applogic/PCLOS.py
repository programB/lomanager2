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


import os
import pathlib
from configuration import logging as log


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


def get_running_package_managers() -> dict:
    # TODO: Implement
    pass


def get_running_Office_processes() -> dict[str, str]:
    binaries_to_check = ["soffice.bin"]
    return get_PID_by_name(binaries_to_check)


def get_system_users() -> list[str]:
    # TODO: Implement
    pass


def is_live_session_active() -> bool:
    # TODO: Verify implementation
    return pathlib.Path("/union").exists()


def get_system_update_status() -> tuple:
    # TODO: Implement
    check_successfull = False
    system_updated = False
    return (check_successfull, system_updated)


def is_lomanager2_latest(lomanger2_version: str) -> bool:
    # TODO: Implement
    return False


def get_disk_space() -> int:
    # TODO: Implement
    return 0


def get_free_space_in_dir(dir) -> int:
    # TODO: Implement
    free_space_kiB = 0
    log.debug(f">>PRETENDING<< free_space_kiB: {free_space_kiB}")
    return free_space_kiB


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
