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
    system_information["is Java installed"] = PCLOS.is_java_installed()

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


def install(
    changes_to_make, tmp_directory, mode, source=None, callback_function=None
) -> dict:
    # TODO: This is dummy implementation for testing
    configuration.logging.warning("WIP. This function sends fake data.")

    # Preparations
    current_progress_is = callback_function
    install_status = {
        "is_install_successful": False,
        "explanation": "Install procedure not executed.",
    }
    # 0) Check mode
    if mode == "local_copy_install":
        # 1 - local_copy_install) Check if files provided by the user can installed
        is_local_copy_usable = verify_local_copy(source)
        if is_local_copy_usable is False:
            message = "Provided packages cannot be installed."
            install_status["explanation"] = message
            configuration.logging.error(message)
            return install_status

    elif mode == "network_install":
        # 1 - network_install) Run collect_packages subprocedure
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
    else:
        message = "Unknown mode."
        install_status["explanation"] = message
        configuration.logging.error(message)
        return install_status

    # At this point network_install and local_copy_install
    # procedures converge
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

    # 5) Run Office install procedure if needed
    any_Office_component_needs_to_be_installed = False

    # TODO: Remove this test code !!!
    configuration.logging.warning(
        f"Adding phony Office package name to install list for tests !"
    )
    changes_to_make["packages_to_install"].append("LibreOffice-9.9-PHONY.rpm")

    for rpm_name in changes_to_make["packages_to_install"]:
        if "LibreOffice" in rpm_name or "Clipart" in rpm_name:
            any_Office_component_needs_to_be_installed = True
            break

    if any_Office_component_needs_to_be_installed is True:
        office_install_status = install_LibreOffice(
            changes_to_make["packages_to_install"], callback_function
        )

        if office_install_status is False:
            message = "Failed to install Office components."
            install_status["explanation"] = message
            configuration.logging.error(message)
            return install_status

    # 6) Any Office base package was affected ?
    # TODO: how to to do that?
    #       Below are just naive checks
    base_package_indentification_string = "SOMETHING"
    if base_package_indentification_string in changes_to_make["packages_to_install"]:
        disable_LO_update_checks()
        add_templates_to_etcskel()
    if base_package_indentification_string in changes_to_make["packages_to_remove"]:
        clean_dot_desktop_files()

    # 7) Should downloaded packages be removed ?
    # TODO: this information has to be passed here from somewhere
    # TODO: Remove this test code !!!
    configuration.logging.warning(f"Manually setting <<keep_packages>> to <<True>>!")
    keep_packages = True
    configuration.logging.warning(
        f"Manually setting <<offline_copy_folder>> to <</tmp/LO_saved_packages>>!"
    )
    offline_copy_folder = "/tmp/LO_saved_packages"
    keep_packages = True
    if keep_packages is True:
        save_copy_for_offline_install(offline_copy_folder)

    # 8) clean up temporary files
    # TODO: Change the hard coded /tmp
    clean_tmp_folder("/tmp")

    message = "All packages successfully installed"
    install_status["is_install_successful"] = True
    install_status["explanation"] = message
    configuration.logging.info(message)
    return install_status


def install_LibreOffice(packages_to_install: list, callback_function) -> bool:
    configuration.logging.warning("WIP. This function sends fake data.")
    # TODO: naming
    current_progress_is = callback_function

    is_every_package_successfully_installed = False
    configuration.logging.debug(f"Packages to install: {packages_to_install}")
    configuration.logging.info("Installing packages...")

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

    is_every_package_successfully_installed = True
    configuration.logging.info("...done installing packages.")

    return is_every_package_successfully_installed


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


def disable_LO_update_checks():
    configuration.logging.warning("WIP. This function sends fake data.")

    print("Preventing LibreOffice from looking for updates on its own...")
    time.sleep(1)
    print("...done.")


def add_templates_to_etcskel():
    # TODO: This function should put a file (smth.xcu) to /etc/skel
    #       in order to have LO properly set up for any new user
    #       accounts created in the OS
    configuration.logging.warning("WIP. This function sends fake data.")

    print("Adding files to /etc/skel ...")
    time.sleep(1)
    print("...done.")


def clean_dot_desktop_files():
    # TODO: This function should remove association between LibreOffice
    #       and Open Document file formats (odt, odf, etc.) from the
    #       global .desktop file (and user files too?)
    configuration.logging.warning("WIP. This function sends fake data.")

    print("Rebuilding menu entries...")
    time.sleep(1)
    print("...done.")


def save_copy_for_offline_install(target_folder):
    # TODO: This function should put all files needed for offline
    #       installation in a structured way into the target_folder
    configuration.logging.warning("WIP. This function sends fake data.")

    print("Saving files for offline install...")
    time.sleep(1)
    print("...done.")


def clean_tmp_folder(tmp_directory):
    # TODO: This function should remove all files from tmp_directory.
    configuration.logging.warning("WIP. This function sends fake data.")

    print("Cleaning temporary files...")
    time.sleep(1)
    print("...done.")


def verify_local_copy(local_copy_directory):
    # TODO: This function should do a rough check whether the folder
    #       provided by the user contains a coherent set of packages needed
    #       for install. This check will be based on file names and expected
    #       folder structure. As such it will not be giving guarantees
    #       of successful install.

    configuration.logging.warning("WIP. This function sends fake data.")

    print("Verifying local copy integrity...")
    time.sleep(1)
    print("...done.")
