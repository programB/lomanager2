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
