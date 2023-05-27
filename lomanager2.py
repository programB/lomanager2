import sys
import logging


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
            normal_install = True
            print("Begin normal installation procedure... ")
        elif choice == 2:
            normal_install = False
            print("Begin installation from local copy... ")
        elif choice == 3:
            print("Begin uninstall procedure... ")
        else:
            time_to_quit = True

    print("Exiting...")
    sys.exit(0)


if __name__ == "__main__":
    main()
