import sys
import logging
import pathlib


def get_current_locale() -> str:
    """Gets currently set system locale.

    It uses environmental variable LC_TELEPHONE
    (following original lomanger bash script in this regard)
    to determine current locale setting for the OS.

    Returns
    -------
    current_locale : str
        A locale identifier eg. "en-GB" or empty string
        if locale could not be determined.
    """

    current_locale = ""
    logging.debug(
        f'Not implemented. Value returned: "{current_locale}" '
        f"({type(current_locale)})"
    )
    return current_locale


def get_system_information() -> dict:
    """Gets information about the OS relevant to LibreOffice installation.

    Returns
    -------
    information : dict
        Useful information
    """

    system_information = dict()
    logging.debug(
        f'Not implemented. Value returned: "{system_information}" '
        f"({type(system_information)})"
    )
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
    logging.debug(
        f"Not implemented.\n"
        f'Value passed: "{dir_path}" '
        f'type: "{type(dir_path)}"\n'
        f'Value passed: "{install_type}" '
        f'type: "{type(install_type)}"\n'
        f'Value returned: "{install_status}" '
        f'type: "{type(install_status)}"\n'
    )
    return install_status


def uninstall_LibreOffice() -> int:
    """Removes LibreOffice from the system.

    Returns
    -------
    uninstall_status : int
       status code
    """

    uninstall_status = -1
    logging.debug(
        f"Not implemented.\n"
        f'Value returned: "{uninstall_status}" '
        f'type: "{type(uninstall_status)}"\n'
    )
    return uninstall_status


def main():
    # Some logging useful to debug this script -
    # - not related to lomanger2 flowchart
    logging.basicConfig(
        format="[%(levelname)s] (in %(funcName)s): %(message)s",
        level=logging.DEBUG,
    )

    # Top level program logic
    # # Set this program's language
    use_language = get_current_locale()

    time_to_quit = False
    while not time_to_quit:
        # # Gather system information
        system_information = get_system_information()

        # # Display system information and choices
        print(f"\nSystem information: {system_information}\n")

        print("This is lomanger2")
        print("What do you want to do?")
        print("1) Install latest version of LibreOffice")
        print("2) Install LibreOffice from locally saved packages")
        print("3) Uninstall LibreOffice from the system")
        print("Any other number) Exit this program")
        while True:
            try:
                choice = int(input("Your choice: "))
                break
            except:
                print("invalid option")

        if choice == 1:
            print("Begin normal installation procedure... ")
            install_dir = pathlib.Path("~/tmp/")
            install_status = install_LibreOffice(
                dir_path=install_dir, install_type="normal"
            )
        elif choice == 2:
            print("Begin installation from local copy... ")
            install_dir = pathlib.Path("~/tmp/")
            install_status = install_LibreOffice(
                dir_path=install_dir, install_type="local-copy"
            )
        elif choice == 3:
            print("Begin uninstall procedure... ")
            uninstall_LibreOffice()
        else:
            time_to_quit = True

    print("Exiting...")
    sys.exit(0)


if __name__ == "__main__":
    main()
