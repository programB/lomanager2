"""Subprocedures for installing/removing packages"""
import time  # TODO: just for the tests
from . import configuration
from . import PCLOS

# TODO: The list of procedures is not complete
# TODO: parameters passed to these functions are
#       just proposals - can/will change


def get_system_information() -> dict:
    """Gets information about the OS relevant to LibreOffice installation.

    Returns
    -------
    information : dict
        Useful information
    """

    system_information = dict()

    # system_information["current locale"] = get_current_locale()
    system_information["live session"] = PCLOS.is_live_session_active()
    # system_information["free HDD space"] = free_HDD_space(install_folder_root)
    system_information["installed software"] = detect_installed_software()
    # system_information["Java installed"] = PCLOS.is_java_installed()

    # fmt: off
    # global _
    # if keep_logging_messages_in_english: _ = gettext.gettext  # switch lang
    # message = _(
    #     "WIP!\n"
    #     "Value returned: {} (type: {})"
    # ).format(system_information, type(system_information))
    # if keep_logging_messages_in_english: del _  # reset lang
    # fmt: on

    # logging.debug(message)
    configuration.logging.warning("WIP !" "May be sending fake data !!!")
    return system_information


def detect_installed_software():
    # TODO: implement
    found_software = [
        ["OpenOffice", "2.0"],
        ["OpenOffice", "2.4", "pl", "gr"],
        ["LibreOffice", "3.0.0", "fr", "de"],
        ["LibreOffice", "7.5", "jp", "pl"],
        ["Clipart", "5.3"],
    ]
    for item in found_software:
        print(item)
    configuration.logging.warning(
        "Function not yet implemented. " "Sending fake data !!!"
    )
    return found_software


def collect_packages(filenames_list, to_directory):
    # TODO: Should this be a list or a dictionary ?
    is_every_package_collected = False
    return is_every_package_collected


def get_Java(to_directory):
    is_java_collected = False
    return is_java_collected


def get_LO_packages(filenames_list, to_directory):
    # TODO: Should this be a list or a dictionary ?
    is_every_package_collected = False
    return is_every_package_collected


def acquire_LO_package(filename, from_http, to_directory):
    is_file_aquired = False
    return is_file_aquired


def install(changes_to_make, tmp_directory, callback_function):
    # TODO: This is dummy implementation for testing
    configuration.logging.warning("WIP. This function sends fake data.")

    current_progress_is = callback_function

    is_install_successfull = False

    total_time_sek = 5
    steps = 30
    for i in range(steps):
        progress = int((i / (steps - 1)) * 100)  # progress in % (0-100)
        time.sleep(total_time_sek / steps)

        # report progress
        # # directly to log
        configuration.logging.info(f"install progress: {progress}%")
        # # using callback if available (emitting Qt signal) 
        if callback_function is not None:
            current_progress_is(progress)

    is_install_successfull = True
    return is_install_successfull


def install_LibreOffice():
    pass


def install_Java():
    pass


def uinstall_LibreOffice():
    pass


def uinstall_Java():
    pass


def install_Clipart():
    pass


def uinstall_Clipart():
    pass
