import sys
import logging
import pathlib
import gettext
import locale
import shutil
from typing import Tuple  # for type hints

# TODO: move all path to a separate object
translations_folder = pathlib.Path("./locales/")
install_folder_root = pathlib.Path("/opt/")
java_executable_file = pathlib.Path("/usr/bin/java")

translation = gettext.translation(
    "lomanager2-main",
    localedir=translations_folder,
)
translation.install()
_ = translation.gettext

keep_logging_messages_in_english = False


def get_current_locale() -> str | None:
    """Gets currently set locale.

    In order to determine current locale
    this function uses locale.getlocale method
    which relies on variable LC_CTYPE.

    Returns
    -------
    language_code : str or None
        A locale identifier eg. "en_GB"
        None is returned if locale could not be determined
        (eg. when LC_CTYPE is set to "C").
    """

    # Note that the original lomanager bash script checks
    # the value of the environmental variable LC_TELEPHONE
    # to determine the language code.
    # If needed this can be done like so (import os):
    # language_code = os.environ["LC_TELEPHONE"].split(".")[0]
    # and check for values that are not language codes
    # like "C" or empty string

    language_code = locale.getlocale()[0]

    # fmt: off
    global _
    if keep_logging_messages_in_english: _ = gettext.gettext  # switch lang
    message = _("Detected language code: {}").format(language_code)
    if keep_logging_messages_in_english: del _  # reset lang
    # fmt: on

    logging.info(message)
    return language_code


def get_system_information() -> dict:
    """Gets information about the OS relevant to LibreOffice installation.

    Returns
    -------
    information : dict
        Useful information
    """

    system_information = dict()

    system_information["current locale"] = get_current_locale()
    system_information["live session"] = is_live_session_active()
    system_information["free HDD space"] = free_HDD_space(install_folder_root)
    system_information["installed office suits"] = detect_installed_office_suits()
    system_information["Java installed"] = is_java_installed()

    # fmt: off
    global _
    if keep_logging_messages_in_english: _ = gettext.gettext  # switch lang
    message = _(
        "WIP!\n"
        "Value returned: {} (type: {})"
    ).format(system_information, type(system_information))
    if keep_logging_messages_in_english: del _  # reset lang
    # fmt: on

    logging.debug(message)
    return system_information


def is_live_session_active() -> bool:
    """Checks is system runs in Live mode aka Live Session.

    Live Session (known before as Live CD) is active when
    the user runs the OS directly of an iso image,
    wihtout installing it onto system drive.
    The hallmark is the existance of /union folder
    created by UnionFS.

    Returns
    -------
    is_active: bool
       True if OS runs in Live Session mode.
    """

    is_active = pathlib.Path("/union").exists()

    # fmt: off
    global _
    if keep_logging_messages_in_english: _ = gettext.gettext  # switch lang
    actv = _("active")
    noactv = _("not active")
    message = _("Live session is: {}").format(actv if is_active else noactv)
    if keep_logging_messages_in_english: del _  # reset lang
    # fmt: on

    logging.info(message)
    return is_active


def free_HDD_space(dir_path: pathlib.Path) -> int:
    """Checks free space on the partition holding a folder passed.

    Returns
    -------
    free_space : int
        Free space in kibibytes (KiB).
    """

    free_space = int(shutil.disk_usage(dir_path).free / 1024)

    # fmt: off
    global _
    if keep_logging_messages_in_english: _ = gettext.gettext  # switch lang
    message = _("Free space at {}: {} KiB").format(str(dir_path), free_space)
    if keep_logging_messages_in_english: del _  # reset lang
    # fmt: on

    logging.info(message)
    return free_space


def is_java_installed() -> bool:
    """Checks if Java Runtime Environment is installed.

    Returns
    -------
    is_java_binary_present : bool
       True if binary is present.
    """

    is_java_binary_present = java_executable_file.exists()

    # fmt: off
    global _
    if keep_logging_messages_in_english: _ = gettext.gettext  # switch lang
    yes = _("is")
    no = _("is not")
    message = _("Java {} installed").format(yes if is_java_binary_present else no)
    if keep_logging_messages_in_english: del _  # reset lang
    # fmt: on

    logging.info(message)
    return is_java_binary_present


def detect_installed_office_suits() -> list[Tuple[str, str]]:
    """Detects legacy OpenOffice and old versions of LibreOffice installed.

    It probes for known set of OpenOffice and LibreOffice versions
    that were part of PCLOS at some point. It does that by
    checking for known executables in known places (eg. /usr/bin/ooffice2*).
    The function returns a list of detected Office suits with version numbers
    (if this could be determined). This list should consist at most 1 entry
    as more would indicate that the user managed to install two different
    versions of Office simultaneously - such option was never supported.

    Returns
    -------
    list_of_detected_suits : list
        List of tuples in the form ("Suite name", "version")
        eg. [("OpenOffice", "2.4"), ("LibreOffice", "7.2")]
    """

    # fmt: off
    global _
    if keep_logging_messages_in_english: _ = gettext.gettext  # switch lang
    # fmt: on

    list_of_detected_suits = list()

    # Look for OpenOffice 2.x (was on 2007 CD)
    if list(pathlib.Path("/usr/bin/").glob("ooffice2*")):
        # exec. detected but if we don't detect version in the version_file
        # we should assume version 2.0
        version = "2.0"
        config_files = list(pathlib.Path("/usr/bin/").glob("ooconfig*"))
        if config_files:
            # get version from the file name
            # (first one only following the original lomanager script)
            version = (str(config_files[0]))[17 : 17 + 3]
        dbg_message = _("Detected OpenOffice series 2 ver.: {}").format(version)
        logging.debug(dbg_message)
        list_of_detected_suits.append(("OpenOffice", version))

    # Look for OpenOffice 3.0.0 (was on 2009.1 CD)
    if pathlib.Path("/usr/bin/ooffice3.0").exists():
        dbg_message = _("Detected OpenOffice ver.: {}").format("3.0.0")
        logging.debug(dbg_message)
        list_of_detected_suits.append(("OpenOffice", "3.0.0"))

    # Look for OpenOffice 3.0.1 and later
    if pathlib.Path("/usr/bin/openoffice.org3").exists():
        # exec. detected but if we don't detect version in the version_file
        # we should assume version 3.1
        version = "3.1"
        # Parse version_file to find version
        # TODO: If 'configparser' module gets included for other purposes
        #       this should be refactored to:
        #       cfg = configparser.ConfigParser()
        #       cfg.read(version_file)
        #       version = cfg.get('Version', 'OOOBaseVersion')
        version_file = "/opt/openoffice.org3/program/versionrc"
        if pathlib.Path(version_file).exists():
            with open(version_file, "r") as f:
                lines = f.readlines()
            for line in lines:
                if "OOOBaseVersion=" in line:
                    version = line.strip().split("=")[-1]
                    break
        dbg_message = _("Detected OpenOffice series 3 ver.: {}").format(version)
        logging.debug(dbg_message)
        list_of_detected_suits.append(("OpenOffice", version))

    # Look for LibreOffice 3.3 (it is intentionally treated separately)
    if pathlib.Path("/usr/bin/libreoffice").exists():
        # exec. detected but if we don't detect version in the version_file
        # we should assume version 3.3
        version = "3.3"
        version_file = "/opt/libreoffice/program/versionrc"  # different then ↑
        # The version extracted from the configuration file should
        # always be 3.3 but the original script checks that anyways
        # and this is why it is done here as well.
        # (Perhaps there were some subvariants like 3.3.1 etc.)
        if pathlib.Path(version_file).exists():
            with open(version_file, "r") as f:
                lines = f.readlines()
            for line in lines:
                if "OOOBaseVersion=" in line:
                    version = line.strip().split("=")[-1]
                    break
        dbg_message = _("Detected LibreOffice series 3.3 ver.: {}").format(version)
        logging.debug(dbg_message)
        list_of_detected_suits.append(("LibreOffice", version))

    # Look for LibreOffice 3.4 and above (including latest)
    # TODO: Move this list to some configuration section or configuration file.
    #       Every time new LibreOffice version is added this list
    #       needs to be updated.
    versions_list = [
        "3.4",
        "3.5",
        "3.6",
        "4.0",
        "4.1",
        "4.2",
        "4.3",
        "4.4",
        "5.0",
        "5.1",
        "5.2",
        "5.3",
        "5.4",
        "6.0",
        "6.1",
        "6.2",
        "6.3",
        "6.4",
        "7.0",
        "7.1",
        "7.2",
        "7.3",
        "7.4",
        "7.5",
    ]
    for version in versions_list:
        if pathlib.Path("/usr/bin/libreoffice" + version).exists():
            dbg_message = _("Detected LibreOffice ver.: {}").format(version)
            logging.debug(dbg_message)
            list_of_detected_suits.append(("LibreOffice", version))

    inf_message = _("Value returned: {} (type: {})").format(
        list_of_detected_suits, type(list_of_detected_suits)
    )
    logging.info(inf_message)

    # fmt: off
    if keep_logging_messages_in_english: del _  # reset lang
    # fmt: on

    return list_of_detected_suits


def install_LibreOffice(dir_path: pathlib.Path, install_type: str) -> int:
    """Runs normal installation procedure of LibreOffice.

    The procedure checks the system for requirements
    that must be met for LibreOffice installation.
    It then either downloads required packages from
    the internet and puts them to the dir_path,
    verifies and installs them
    or installs from locally stored packages.
    For "normal" mode the OS must be fully updated for the
    procedure to succeed,
    for "local-copy" install this check is skipped.

    Parameters
    ----------
    dir_path : pathlib.Path or str
        A path to an existing directory to where packages will be downloaded
        and installed from or where they are already present.

    install_type : {"normal", "local-copy"}
        Determines type of install. "normal" means LibreOffice
        packages will be downloaded from the internet
        if set to "local-copy" locally stored packages will be used.

    Returns
    -------
    install_status : int
       status code
    """

    install_status = -1

    # fmt: off
    global _
    if keep_logging_messages_in_english: _ = gettext.gettext  # switch lang
    message = _(
        "NOT IMPLEMENTED!\n"
        "Value 1 passed: {} (type: {})\n"
        "Value 2 passed: {} (type: {})\n"
        "Value returned: {} (type: {})"
    ).format(dir_path, type(dir_path), install_type, type(install_type),
             install_status, type(install_status))
    if keep_logging_messages_in_english: del _  # reset lang
    # fmt: on

    logging.debug(message)
    return install_status


def uninstall_LibreOffice() -> int:
    """Removes LibreOffice from the system.

    Returns
    -------
    uninstall_status : int
       status code
    """

    uninstall_status = -1

    # fmt: off
    global _
    if keep_logging_messages_in_english: _ = gettext.gettext  # switch lang
    message = _(
        "NOT IMPLEMENTED!\n"
        "Value returned: {} (type: {})"
    ).format(uninstall_status, type(uninstall_status))
    if keep_logging_messages_in_english: del _  # reset lang
    # fmt: on

    logging.debug(message)
    return uninstall_status


# Top level program logic
# # Start
def main():
    # Some logging useful to debug this script -
    # - not related to lomanager2 flowchart
    logging.basicConfig(
        format="[%(levelname)s](%(asctime)s) (in %(funcName)s): %(message)s",
        level=logging.DEBUG,
    )

    # # Set this program's language
    # # (This is done at the top of the module by setting up gettext)

    # # Enter main loop
    time_to_quit = False
    while not time_to_quit:
        # # Gather system information
        system_information = get_system_information()

        # # Display system information and choices
        print(f"\nSystem information: {system_information}\n")

        # # Get user input
        print(_("This is lomanager2"))
        print(_("What do you want to do?"))
        print(_("1) Install latest version of LibreOffice"))
        print(_("2) Install LibreOffice from locally saved packages"))
        print(_("3) Uninstall LibreOffice from the system"))
        print(_("Any other number) Exit this program"))
        while True:
            try:
                choice = int(input(_("Your choice: ")))
                break
            except:
                print(_("invalid option"))

        if choice == 1:
            print(_("Begin normal installation procedure... "))
            install_dir = pathlib.Path("~/tmp/")
            install_status = install_LibreOffice(
                dir_path=install_dir, install_type="normal"
            )
        elif choice == 2:
            print(_("Begin installation from local copy... "))
            install_dir = pathlib.Path("~/tmp/")
            install_status = install_LibreOffice(
                dir_path=install_dir, install_type="local-copy"
            )
        elif choice == 3:
            print(_("Begin uninstall procedure... "))
            uninstall_LibreOffice()
        else:
            # # User chooses to exit ?
            time_to_quit = True

    # # End
    print(_("Exiting..."))
    sys.exit(0)


if __name__ == "__main__":
    main()
