"""Subprocedures for installing/removing packages"""
import pathlib
import time  # TODO: just for the tests
import re
import configuration
from . import PCLOS

# TODO: The list of procedures is not complete
# TODO: parameters passed to these functions are
#       just proposals - can/will change


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


def local_copy_install_procedure(
    virtual_packages,
    tmp_directory,
    keep_packages,
    install_mode,
    local_copy_directory,
    callback_function=None,
) -> dict:
    # TODO: This is dummy implementation for testing
    configuration.logging.debug("WIP !")

    # Preparations

    current_progress_is = callback_function
    install_status = {
        "is_install_successful": False,
        "explanation": "Install procedure not executed.",
    }

    # Perform rough verification of local copy directory
    is_Java_present = False
    is_LibreOffice_core_present = False
    is_LibreOffice_lang_present = False
    is_Clipart_present = False
    # local_copy_directory exists?
    if pathlib.Path(local_copy_directory).is_dir():
        (
            is_Java_present,
            is_LibreOffice_core_present,
            is_LibreOffice_lang_present,
            is_Clipart_present,
        ) = verify_local_copy(local_copy_directory)
    else:
        message = "Could not find directory with saved packages."
        install_status["explanation"] = message
        configuration.logging.error(message)
        return install_status

    # Mark virtual packages accordingly to the
    # content of local_copy_directory and system state
    if is_LibreOffice_core_present is False:
        # There are no LibreOffice core packages in local_copy_directory but
        # perhaps the user meant to install Openclipart library?
        if is_Clipart_present is False:
            message = (
                "Neither LibreOffice nor Openclipart library were found "
                "in the folder provided."
            )
            install_status["explanation"] = message
            configuration.logging.error(message)
            return install_status
        else:  # Clipart packages found in local_copy_directory
            # FIXME: Currently there is no guarantee clipart virtual package
            #       will be in virtual_packages.
            #       This is a problem and must be fixed in PackageMenu
            #       And what if it exists? Should it be upgraded ?
            configuration.logging.debug(
                "Openclipart rpms found and marked for installation."
            )
            for package in virtual_packages:
                if package.family == "Clipart":
                    package.is_marked_for_removal = False
                    package.is_marked_for_upgrade = False
                    package.is_marked_for_install = True
                    package.is_to_be_downloaded = False

    if is_LibreOffice_core_present is True:
        # Assuming user wants to install LibreOffice from local_copy_directory.
        # This is possible only if Java is present in the OS or
        # can be installed from local_copy_directory
        if PCLOS.is_java_installed() is False and is_Java_present is False:
            message = (
                "Java is not installed in the system and was not be found in "
                "the directory provided."
            )
            install_status["explanation"] = message
            configuration.logging.error(message)
            return install_status
        elif PCLOS.is_java_installed() is False and is_Java_present is True:
            # Java not installed but can be installed from local_copy_directory
            # FIXME: Java virtual package in not guaranteed to exist in
            #        virtual_packages. FIX this.
            configuration.logging.debug("Java rpms found and marked for installation.")
            for package in virtual_packages:
                if package.family == "Java":
                    package.is_marked_for_removal = False
                    package.is_marked_for_upgrade = False
                    package.is_marked_for_install = True
                    package.is_to_be_downloaded = False

        elif PCLOS.is_java_installed() is True and is_Java_present is False:
            configuration.logging.debug("Java already installed.")
            for package in virtual_packages:
                if package.family == "Java":
                    package.is_marked_for_removal = False
                    package.is_marked_for_upgrade = False
                    package.is_marked_for_install = False
                    package.is_to_be_downloaded = False
        else:
            # TODO Java is installed AND is present in local_copy_directory
            #      what should be done it such a case? Reinstall?
            #      Try using rpm -Uvh which will update it if package is newer?
            #      Skipping for now.
            pass

        configuration.logging.debug(
            "Marking all existing OpenOffice and LibreOffice packages for removal."
        )
        for package in virtual_packages:
            if package.family == "OpenOffice" or package.family == "LibreOffice":
                package.is_marked_for_removal = True
                package.is_marked_for_upgrade = False
                package.is_marked_for_install = False
                package.is_to_be_downloaded = False

        configuration.logging.debug("Marking LibreOffice core for install.")
        # FIXME: Which package to mark? virtual_packages only contains
        #        list of installed packages (which by itself should be changes
        #        for different reason) and the version number of the
        #        LO core in the local_copy_directory is unknown.
        #        Parse the filename? add "0.0.0.0" as indicating local copy
        #        install?
        for package in virtual_packages:
            if package.family == "OpenOffice" and package.kind == "core-packages":
                package.is_marked_for_removal = False
                package.is_marked_for_upgrade = False
                package.is_marked_for_install = True
                package.is_to_be_downloaded = False

        configuration.logging.debug("DO SOMETHING HERE")
        if is_LibreOffice_lang_present:
            # User has also saved some language packs. Install them all.
            # TODO: mark them for install but not for download
            # FIXME: Again which packages to mark? virtual_packages only contains
            #        list of installed packages (which by itself should be changes
            #        for different reason) and the version number of the
            #        LO core in the local_copy_directory is unknown.
            #        Parse the filename? add "0.0.0.0" as indicating local copy
            #        install?
            configuration.logging.debug("DO SOMETHING HERE")
        if is_Clipart_present:
            # User has also saved clipart package. Install it.
            # TODO: mark clipart for installation/upgrade accordingly
            # FIXME: Again which package to mark? virtual_packages only contains
            #        list of installed packages (which by itself should be changes
            #        for different reason) and the version number of the
            #        LO core in the local_copy_directory is unknown.
            #        Parse the filename? add "0.0.0.0" as indicating local copy
            #        install?
            configuration.logging.debug("DO SOMETHING HERE")

    # TODO: should it now converge with the network_install procedure ?

    return install_status


def uinstall_LibreOffice():
    pass


def uinstall_Java():
    pass


def install_Clipart():
    pass


def uinstall_Clipart():
    pass


def verify_local_copy(local_copy_directory: str) -> tuple[bool, bool, bool, bool]:
    """Checks for presence of saved packages based on file name convention

    Functions checks for:
        - 2 Java rpm packages
        - any LibreOffice core package
        - LibreOffice langs/help packs folder
        - 2 clipart rpm packages
    based on their expected files names (No version checking is performed).
    Returned is True/False for every of above 4 components.
    True means component can be installed from local_copy_directory.

    Parameters
    ----------
    local_copy_directory : str
      Directory containing saved packages

    Returns
    -------
    tuple[bool,bool,bool,bool]
      (T) for each: Java, LibreOffice core, LibreOffice langs, Clipart if
      suitable for install from local_copy_directory (F) otherwise
    """

    configuration.logging.debug("WIP")

    is_Java_present = False
    is_LibreOffice_core_present = False
    is_LibreOffice_lang_present = False
    is_Clipart_present = False

    configuration.logging.debug("Verifying local copy ...")
    # 1) Directory for Java rpms exist inside?
    # (Java_RPMS as directory name is set here as a standard)
    Java_dir = pathlib.Path(local_copy_directory).joinpath("Java_RPMS")
    configuration.logging.debug(f"Java RPMS dir: {Java_dir}")
    if Java_dir.is_dir():
        # Files: task-java-<something>.rpm ,  java-sun-<something>.rpm
        # are inside? (no specific version numbers are assumed or checked)
        is_task_java_present = any(
            ["task-java" in file.name for file in Java_dir.iterdir()]
        )
        is_java_sun_present = any(
            ["java-sun" in file.name for file in Java_dir.iterdir()]
        )
        # Only if both are present we conclude Java can be installed
        # from the local copy directory.
        is_Java_present = all([is_task_java_present, is_java_sun_present])

    # 2) LibreOffice core packages folder
    LO_core_dir = pathlib.Path(local_copy_directory).joinpath("LO_core_TGZS")
    if LO_core_dir.is_dir():
        # Check for tar.gz archive with core packages
        regex = re.compile("LibreOffice_[0-9]*.[0-9]*.[0-9]*_Linux_x86-64_rpm.tar.gz")
        is_LibreOffice_core_present = any(
            [regex.search(file.name) for file in LO_core_dir.iterdir()]
        )

    # 3) LibreOffice lang and help packages folder
    #    (its content is not critical for the decision procedure
    #     so just check if it exists and is non empty)
    LO_lang_dir = pathlib.Path(local_copy_directory).joinpath("LO_lang_TGZS")
    is_LibreOffice_lang_present = LO_lang_dir.is_dir() and any(LO_lang_dir.iterdir())

    # 4) Clipart directory
    Clipart_dir = pathlib.Path(local_copy_directory).joinpath("Clipart_RPMS")
    if Clipart_dir.is_dir():
        # Files: libreoffice-openclipart-<something>.rpm ,
        # clipart-openclipart-<something>.rpm
        # are inside? (no specific version numbers are assumed or checked)
        is_lo_clipart_present = any(
            ["libreoffice-openclipart" in file.name for file in Clipart_dir.iterdir()]
        )
        is_openclipart_present = any(
            ["clipart-openclipart" in file.name for file in Clipart_dir.iterdir()]
        )
        # Only if both are present clipart library can be installed
        # from the local copy directory.
        is_Clipart_present = all([is_lo_clipart_present, is_openclipart_present])

    configuration.logging.debug(f"Java is present: {is_Java_present}")
    configuration.logging.debug(f"LO core is present: {is_LibreOffice_core_present}")
    configuration.logging.debug(f"LO langs is present: {is_LibreOffice_lang_present}")
    configuration.logging.debug(f"Clipart lib is present: {is_Clipart_present}")
    return (
        is_Java_present,
        is_LibreOffice_core_present,
        is_LibreOffice_lang_present,
        is_Clipart_present,
    )
