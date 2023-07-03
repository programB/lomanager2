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


def collect_packages(
    packages_to_download: list, tmp_directory, callback_function
) -> bool:
    configuration.logging.warning("WIP. This function sends fake data.")

    is_every_package_collected = False

    print(f"Packages to download: {packages_to_download}")
    print("Collecting packages...")
    time.sleep(2)
    print("...done collecting packages.")

    is_every_package_collected = True
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


def install(changes_to_make, tmp_directory, callback_function) -> dict:
    # TODO: This is dummy implementation for testing
    configuration.logging.warning("WIP. This function sends fake data.")

    # Preparations
    current_progress_is = callback_function
    install_status = {
        "is_install_successful": False,
        "explanation": "Install procedure not executed.",
    }

    # 1) Run collect_packages subprocedure
    # TODO: Is it always true that packages_to_download <=> packages_to_install
    packages_to_download = changes_to_make["packages_to_install"]
    # TODO: Should it be a different function or perhaps
    #       callback_function should take some parameters other then
    #       integer representing percentage progress eg. a dictionary
    #       with information what progress is being reported:
    #       download, install, a what file etc..
    download_progress_callback = callback_function
    collect_status = collect_packages(
        packages_to_download,
        tmp_directory,
        download_progress_callback,
    )
    if collect_status is False:
        message = "Failed to download all requested packages."
        install_status["explanation"] = message
        configuration.logging.error(message)
        return install_status

    # 2) detect and terminate (kill -9) LibreOffice quickstarter
    terminate_LO_quickstarter()

    # 3) Run Java install procedure if needed
    is_Java_install_required = False

    # TODO: Remove this test code !!!
    configuration.logging.warning(f"Adding phony Java package name for tests !")
    changes_to_make["packages_to_install"].append("Java-1.0-PHONY.rpm")

    # if any([True for rpm_name in changes_to_make["packages_to_install"] if "Java" in rpm_name])
    for rpm_name in changes_to_make["packages_to_install"]:
        if "Java" in rpm_name:
            is_Java_install_required = True
            break

    if is_Java_install_required is True:
        java_install_status = install_Java()

        if java_install_status is False:
            message = "Failed to install Java."
            install_status["explanation"] = message
            configuration.logging.error(message)
            return install_status

    # At this point everything needed is downloaded and verified
    # and Java is installed in the system.
    # We can remove old Office components
    # in preparation for the install step.
    # 4) Run Office uninstall procedure if needed
    any_Office_component_needs_to_be_removed = False

    # TODO: Remove this test code !!!
    configuration.logging.warning(
        f"Adding phony Office package name to uninstall list for tests !"
    )
    changes_to_make["packages_to_remove"].append("OpenOffice-3.0-PHONY.rpm")

    for rpm_name in changes_to_make["packages_to_remove"]:
        if "Office" in rpm_name:
            any_Office_component_needs_to_be_removed = True
            break

    if any_Office_component_needs_to_be_removed is True:
        office_removal_status = office_uninstall(
            changes_to_make["packages_to_remove"], callback_function
        )

        # If the procedure failed completely (no packages got uninstalled)
        # there is no problem - system state has not changed.
        # If however it succeeded but only partially this is a problem because
        # Office might have gotten corrupted and is no longer working and new
        # Office will not be installed. Recovery from such a condition is
        # likely to require manual user intervention - not good.
        # TODO: Can office_uninstall procedure be made to have dry-run option
        #       to make sure that uninstall is atomic (all or none)?
        if office_removal_status is False:
            message = "Failed to remove Office components."
            install_status["explanation"] = message
            configuration.logging.error(message)
            return install_status

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

    message = "All packages successfully installed"
    install_status["is_install_successful"] = True
    install_status["explanation"] = message
    configuration.logging.info(message)
    return install_status


def install_LibreOffice():
    pass


def install_Java() -> bool:
    configuration.logging.warning("WIP. This function sends fake data.")

    is_java_successfully_installed = False
    configuration.logging.info("Starting Java install procedure...")

    time.sleep(2)

    is_java_successfully_installed = True
    configuration.logging.info("Java successfully installed.")

    return is_java_successfully_installed


def uinstall_LibreOffice():
    pass


def uinstall_Java():
    pass


def install_Clipart():
    pass


def uinstall_Clipart():
    pass


def terminate_LO_quickstarter():
    configuration.logging.warning("WIP. This function sends fake data.")

    print("Checking for LibreOffice quickstarter process...")
    print("LibreOffice quickstarter is running (PID: ABCD)")
    print("Terminating LibreOffice quickstarter...")
    time.sleep(2)
    print("...done.")


def office_uninstall(packages_to_remove: list, callback_function) -> bool:
    configuration.logging.warning("WIP. This function sends fake data.")

    is_every_package_successfully_removed = False
    configuration.logging.debug(f"Packages to remove: {packages_to_remove}")
    configuration.logging.info("Removing packages...")

    time.sleep(2)

    is_every_package_successfully_removed = True
    configuration.logging.info("...done removing packages.")

    return is_every_package_successfully_removed
