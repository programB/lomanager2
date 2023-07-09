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
