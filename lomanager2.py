import sys
import logging
import pathlib
import gettext
import locale

# TODO: move all path to a separate object
translations_folder = pathlib.Path("./locales/")

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

    # fmt: off
    global _
    if keep_logging_messages_in_english: _ = gettext.gettext  # switch lang
    message = _(
        "NOT IMPLEMENTED!\n"
        "Value returned: {} (type: {})"
    ).format(system_information, type(system_information))
    if keep_logging_messages_in_english: del _  # reset lang
    # fmt: on

    logging.debug(message)
    return system_information


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


def main():
    # Some logging useful to debug this script -
    # - not related to lomanager2 flowchart
    logging.basicConfig(
        format="[%(levelname)s](%(asctime)s) (in %(funcName)s): %(message)s",
        level=logging.DEBUG,
    )

    # Top level program logic
    # # Set this program's language
    preferred_language = get_current_locale()

    # In case locale settings are messed up default to en_US
    if preferred_language is None:
        preferred_language = "en_US"

    time_to_quit = False
    while not time_to_quit:
        # # Gather system information
        system_information = get_system_information()

        # # Display system information and choices
        print(f"\nSystem information: {system_information}\n")

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
            time_to_quit = True

    print(_("Exiting..."))
    sys.exit(0)


if __name__ == "__main__":
    main()
