"""
This module gathers functions to return some information about current
operating system state or change that state.
"""

import logging
import os
import pathlib
import pwd
import re
import shutil
import subprocess
import tarfile
from typing import Callable

import configuration

log = logging.getLogger("lomanager2_logger")


def run_shell_command(
    cmd: str, shell="bash", timeout=20, err_check=True
) -> tuple[bool, str]:
    if cmd:
        full_command = [shell] + ["-c"] + [cmd]
        log.debug(f"Attempting to execute command: {full_command}")

        try:
            shellcommand = subprocess.run(
                full_command,
                check=err_check,  # some commands return non-zero exit code if successful
                timeout=timeout,  # fail on command taking to long to exec.
                capture_output=True,  # capture both stdout and stderr
                text=True,  # give the output as a string not bytes
                encoding="utf-8",
            )
            answer = (shellcommand.stdout + shellcommand.stderr).strip()
            log.debug(f"Received answer: {answer}")
            return (True, answer)
        except FileNotFoundError as exc:
            msg = "Executable not be found. " + str(exc)
            log.error(msg)
            return (False, msg)
        except subprocess.CalledProcessError as exc:
            msg = "Error: " + str(exc)
            log.error(msg)
            return (False, msg)
        except subprocess.TimeoutExpired as exc:
            msg = str(exc)
            log.error(msg)
            return (False, msg)
    else:
        msg = "An empty string passed as a command to be executed!"
        log.error(msg)
        return (False, msg)


def get_PIDs_by_name(names: list[str]) -> dict:
    """Checks PIDs of any running processes passed by executable names."""

    running_processes = {}
    for name in names:
        status, pids = run_shell_command("pidof " + name, err_check=False)
        if status:
            running_processes[name] = pids.split()
        else:
            return {"Error": [pids]}
    log.debug(running_processes)
    return running_processes


def get_running_package_managers() -> tuple[bool, dict]:
    """Checks if any package manager is running"""
    package_managers = [
        "synaptic",
        "smart",
        "ksmarttray",
        "kpackage",
        "apt-get",
    ]
    running_managers = {}
    returned_pids = get_PIDs_by_name(package_managers)
    is_successful = True if not "Error" in returned_pids.keys() else False
    if is_successful:
        for key, item in returned_pids.items():
            if item:
                running_managers[key] = ", ".join(item)
    log.debug(f"running managers: {running_managers}")
    return (is_successful, running_managers)


def get_running_Office_processes() -> tuple[bool, dict]:
    """Checks if any Office is running"""
    binaries_to_check = ["soffice.bin"]
    running_office_suits = {}
    returned_pids = get_PIDs_by_name(binaries_to_check)
    is_successful = not "Error" in running_office_suits.keys()
    if is_successful:
        for key, item in returned_pids.items():
            if item:
                log.debug(f"ITEM: {item}, {type(item)}")
                running_office_suits[key] = ", ".join(item)
    return (is_successful, running_office_suits)


class HumanUser:
    def __init__(self, name, home_dir) -> None:
        self.name = name
        self.home_dir = pathlib.Path(home_dir)


def get_system_users() -> list[HumanUser]:
    """Looks for regular (not services) system users.

    The criteria are that the user has a login shell that is one
    of the shells listed in /etc/shells and has a home directory in /home.
    Additionally root user is included.
    """
    system_shells = []
    with open("/etc/shells", "r") as f:
        for line in f:
            line = line.strip()
            if line and line.startswith("/"):
                system_shells.append(line)

    human_users = []
    for user in pwd.getpwall():
        if (user.pw_shell in system_shells) and ("home" in user.pw_dir):
            human_users.append(HumanUser(user.pw_name, user.pw_dir))
    try:
        root_user = pwd.getpwuid(0)  # assuming root has uid 0
    except Exception as error:
        log.error("No root user found " + str(error))
    else:
        human_users.append(HumanUser(root_user.pw_name, root_user.pw_dir))
    return human_users


def is_live_session_active() -> bool:
    return pathlib.Path("/union").exists()


def check_system_update_status() -> tuple[bool, bool, str]:
    # Since the apt-get update command fetches data from
    # repo server it make take a while hence setting timeout to 45 sek.
    status, output = run_shell_command("apt-get update", timeout=45, err_check=False)
    if status:
        if any(
            map(lambda e: e in output, ["error", "Error", "Err", "Failure", "failed"])
        ):
            return (False, False, "Failed to check updates")

        status, output = run_shell_command(
            "apt-get dist-upgrade --fix-broken --simulate", err_check=True
        )
        if status:
            check_successful = True
            system_updated = False
            explanation = "Unexpected output of apt-get command: " + output
            regex_update = re.compile(
                r"^(?P<n_upgraded>[0-9]+) upgraded, (?P<n_installed>[0-9]+) newly installed, (?P<n_removed>[0-9]+) removed and (?P<n_not_upgraded>[0-9]+) not upgraded\.$"
            )
            # If OS is fully updated the summary line in the output should be:
            # "0 upgraded, 0 newly installed, 0 removed and 0 not upgraded."
            for line in output.split("\n"):
                if match := regex_update.search(line):
                    n_upgraded = match.group("n_upgraded")
                    n_installed = match.group("n_installed")
                    n_removed = match.group("n_removed")
                    n_not_upgraded = match.group("n_not_upgraded")
                    if not (
                        n_upgraded == n_installed == n_removed == n_not_upgraded == "0"
                    ):
                        system_updated = False
                        explanation = "System not fully updated"
                        break
                    else:
                        system_updated = True
                        explanation = "System updated"
                        break
        else:
            check_successful = False
            system_updated = False
            explanation = output
            log.error(output)

    else:
        check_successful = False
        system_updated = False
        explanation = output
        log.error(output)
    return (check_successful, system_updated, explanation)


def free_space_in_dir(dir: pathlib.Path) -> int:
    """Return free disk space for the partition holding dir.

    Returns
    -------
    free_space : int
        Free space in bytes
    """

    free_space = int(shutil.disk_usage(dir).free)
    log.debug(f"free space in {dir}: {free_space} bytes")
    return free_space


def detect_installed_java() -> tuple[bool, str]:
    found = pathlib.Path("/usr/bin/java").exists()
    # Since this program is not meant to update Java,
    # Java version is not being detected.
    java_version = ""
    log.debug(f"Is Java installed?: {found}")
    return (found, java_version)


def detect_installed_office_software() -> list[tuple[str, str, tuple]]:
    """Checks for installed OpenOffice and LibreOffice version

    This function checks the presence of certain files, directories
    and rpm packages that indicate OpenOffice/LibreOffice of specific
    version is installed. Those checks are based on which version
    of aforementioned software was offered by PCLOS

    Returns
    -------
    list[tuple[str, str, tuple]]
    List of detected Offices. LibreOffice/OpenOffice, version string,
    tuple of language codes for this version
    """

    list_of_detected_suits = []

    # Look for OpenOffice 2.x (was on 2007 CD)
    if list(pathlib.Path("/usr/bin/").glob("ooffice2*")):
        # Executable detected but if the version can't be determined
        # by parsing version_file version 2.0 should be assumed.
        version = "2.0"
        config_files = list(pathlib.Path("/usr/bin/").glob("ooconfig*"))
        if config_files:
            # get version from the file name:
            # - the way original lomanager does it
            # - take the first file in the list if more then one detected
            version = (str(config_files[0]))[17 : 17 + 3]
        dbg_message = ("Detected OpenOffice series 2 ver.: {}").format(version)
        log.debug(dbg_message)
        # No attempt will be made to detect language packs -> ()
        list_of_detected_suits.append(("OpenOffice", version, ()))

    # Look for OpenOffice 3.0.0 (was on 2009.1 CD)
    if pathlib.Path("/usr/bin/ooffice3.0").exists():
        dbg_message = ("Detected OpenOffice ver.: {}").format("3.0.0")
        log.debug(dbg_message)
        # No attempt will be made to detect language packs -> ()
        list_of_detected_suits.append(("OpenOffice", "3.0.0", ()))

    # Look for OpenOffice 3.0.1 and later
    if pathlib.Path("/usr/bin/openoffice.org3").exists():
        # Executable detected but if the version can't be determined
        # by parsing version_file version 3.1 should be assumed.
        version = "3.1"
        # Parse version_file to find version
        # TODO: If 'configparser' module gets included for other purposes
        #       this should get refactored to:
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
        dbg_message = ("Detected OpenOffice series 3 ver.: {}").format(version)
        log.debug(dbg_message)
        # No attempt will be made to detect language packs -> ()
        list_of_detected_suits.append(("OpenOffice", version, ()))

    # Look for LibreOffice 3.3 (it is intentionally treated separately)
    if pathlib.Path("/usr/bin/libreoffice").exists():
        # Executable detected but if the version can't be determined
        # by parsing version_file version 3.3 should be assumed.
        version = "3.3"
        version_file = "/opt/libreoffice/program/versionrc"  # different then↑
        # The version extracted from the configuration file should
        # always be 3.3 but the original lomanager script checks that anyways,
        # so this is why it is done here as well.
        # (Perhaps there were some subvariants like 3.3.1 etc.)
        if pathlib.Path(version_file).exists():
            with open(version_file, "r") as f:
                lines = f.readlines()
            for line in lines:
                if "OOOBaseVersion=" in line:
                    version = line.strip().split("=")[-1]
                    break
        dbg_message = ("Detected LibreOffice series 3.3 ver.: {}").format(version)
        log.debug(dbg_message)
        # No attempt will be made to detect language packs -> ()
        list_of_detected_suits.append(("LibreOffice", version, ()))

    # Look for LibreOffice 3.4 and above (including latest)
    if pathlib.Path("/usr/bin").glob("libreoffice*"):
        log.debug("Detected LibreOffice binary")
        # Check if the ure rpm package is installed
        success, reply = run_shell_command("rpm -qa | grep libreoffice | grep ure")
        if success and reply:
            log.debug("LibreOffice's ure package is installed")
            # Get LibreOffice's full version string by quering this rpm package
            ure_package_str = reply.split("\n")[0]
            success, reply = run_shell_command(
                f"rpm -q {ure_package_str} --qf %{{version}}"
            )
            full_version = reply.strip()
            base_version = configuration.make_base_ver(full_version)
            log.debug(f"LibreOffice version read from ure package: {full_version}")

            log.debug("Checking for language packs installed for that version")
            success, reply = run_shell_command(
                f"rpm -qa | grep libreoffice{base_version}", err_check=False
            )
            if success and reply:
                regex_lang = re.compile(
                    rf"^libreoffice{base_version}-(?P<det_lang>[a-z]{{2,3}})(?P<det_regio>\-[a-zA-Z]*)?-{full_version}[0-9\-]*[0-9]$"
                )
                # example matches:
                # libreoffice7.5-fr-7.5.4.2-2
                # #  det_lang = "fr" det_regio = ""
                # (the digit after the last "-" is the rpm release version
                # and is of no interest)
                # libreoffice7.4-ca-valencia-7.4.4.2-2
                # #  det_lang = "ca" det_regio = "-valencia"
                # libreoffice7.4-en-GB-7.4.4.2-2
                # #  det_lang = "en" det_regio = "-GB"
                # libreoffice7.4-kmr-Latn-7.4.4.2-2
                # #  det_lang = "kmr" det_regio = "-Latn"
                # ALSO !:
                # libreoffice7.5-ure-7.5.4.2-2
                # this is not a language package
                # Alternative approach would be to do another query for
                # every package detected like so:
                # rpm -q <package> --qf %{summary}
                # and rely on summary for language packages being:
                # "Brand language module"
                # regex is still needed though to extract det_lang and det_regio
                # For now we just explicitly exclude those pesky packages
                non_lang_packages = ["ure"]
                langs_found = []
                for package in reply.split("\n"):
                    if match := regex_lang.search(package):
                        det_lang = match.group("det_lang")
                        det_regio = match.group("det_regio")
                        if det_lang not in non_lang_packages:
                            if det_regio:
                                det_lang = det_lang + det_regio
                            # en-US language pack it is only installed/removed
                            # together with core package and should
                            # not be treated as a standalone addition
                            if det_lang != "en-US":
                                log.debug(f"Found language {det_lang}")
                                langs_found.append(det_lang)
                list_of_detected_suits.append(
                    (
                        "LibreOffice",
                        full_version,
                        tuple(langs_found),
                    )
                )
            else:
                # No langs detected just add the core package to the list
                list_of_detected_suits.append(("LibreOffice", full_version, ()))
        else:
            log.warning("LibreOffice binary detected but no installed rpm found.")

    inf_message = ("All detected office suits (and langs): {}").format(
        list_of_detected_suits
    )
    log.debug(inf_message)
    return list_of_detected_suits


def detect_installed_clipart() -> tuple[bool, str]:
    """Checks if libreoffice-openclipart rpm package is installed"""
    success, reply = run_shell_command(
        "rpm -qa | grep libreoffice-openclipart", err_check=False
    )
    if success and reply:
        lca_regeX = re.compile(
            r"^libreoffice-openclipart-(?P<ver_lca>[0-9]+\.[0-9]+)-[0-9]+pclos20[0-9][0-9]"
        )
        if match := lca_regeX.search(reply.split("\n")[0]):
            found = True
            clipart_version = match.group("ver_lca")
            log.debug(f"Openclipart library version {clipart_version} is installed")
        else:
            found = False
            clipart_version = ""
    else:
        found = False
        clipart_version = ""
    return (found, clipart_version)


def remove_file(path: pathlib.Path) -> bool:
    allowed_dirs = [
        pathlib.Path("/tmp"),
        pathlib.Path("/opt").glob("openoffice*"),
        pathlib.Path("/opt").glob("libreoffice*"),
        pathlib.Path("/etc/skel"),
        pathlib.Path("/etc/skel_fm"),
        pathlib.Path("/etc/skel_default"),
        pathlib.Path("/etc/skel-orig"),
        pathlib.Path("/usr/share/icons"),
        pathlib.Path("user_home/Desktop"),
        pathlib.Path("user_home/.config"),
        pathlib.Path("user_home/.kde4"),
        pathlib.Path("user_home/.libreoffice"),
    ]
    for user in get_system_users():
        allowed_dirs.append(user.home_dir.glob(".ooo*"))

    path = path.expanduser()

    if not any(map(path.is_relative_to, allowed_dirs)):
        log.error(
            f"This program should not be trying to remove files from this "
            f"location! Refusing to remove: {path}"
        )
        is_removed = False
    else:
        try:
            os.remove(path)
            is_removed = True
        except Exception as error:
            msg = f"Error when removing {path}: "
            log.error(msg + str(error))
            is_removed = False
    return is_removed


def move_file(from_path: pathlib.Path, to_path: pathlib.Path) -> bool:
    try:
        shutil.move(src=from_path, dst=to_path)
        is_moved = True
    except Exception as error:
        msg = f"Error when moving {from_path} to {to_path}: "
        log.error(msg + str(error))
        is_moved = False
    return is_moved


def create_dir(dir_path: pathlib.Path):
    log.debug(f"Creating: {dir_path}")
    os.makedirs(dir_path, exist_ok=True)


def move_dir(from_path: pathlib.Path, to_path: pathlib.Path) -> tuple[bool, str]:
    try:
        if from_path.exists():
            force_rm_directory(to_path)
        shutil.move(src=from_path, dst=to_path)
        is_moved = True
        msg = ""
    except Exception as error:
        msg = f"Error when moving {from_path} to {to_path}: "
        log.error(msg + str(error))
        is_moved = False
    return (is_moved, msg)


def run_shell_command_with_progress(
    cmd: str,
    progress_reporter: Callable,
    parser: Callable,
    byte_output=False,
    shell="bash",
) -> tuple[bool, str]:
    full_command = [shell] + ["-c"] + [cmd]
    fulloutput = []
    # control characters excluding new line char "\n"
    ctrl_chars = (
        list(map(chr, range(0, 9)))
        + list(map(chr, range(11, 32)))
        + list(map(chr, range(127, 160)))
    )

    with subprocess.Popen(
        full_command,
        bufsize=1,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=False,
        universal_newlines=not byte_output,
    ) as proc:
        concat_normal_chars = b""
        while proc.poll() is None:
            if byte_output:
                output = proc.stdout.read(1)
                fulloutput.append(output.decode("utf-8"))
                if parser and output.decode("utf-8") not in ctrl_chars:
                    # Don't bother calling parser when receiving control chars
                    concat_normal_chars += output
                    label, percentage = parser(concat_normal_chars)
                    if label != "no match":
                        progress_reporter.progress_msg(label, prc=str(percentage))
                        progress_reporter.progress(percentage)
            else:  # strings
                output = proc.stdout.readline()
                fulloutput.append(output)
                if parser:
                    label, percentage = parser(output)
                    if label != "no match":
                        progress_reporter.progress_msg(label, prc=str(percentage))
                        progress_reporter.progress(percentage)
    return (True, "".join(fulloutput))


def install_using_apt_get(
    package_nameS: list,
    progress_reporter: Callable,
):
    """Install rpm packages using apt-get command provided by the OS

    This function first performs dry-run to check if the list of
    rpm packages provided can be installed and if so proceeds with
    actual install reporting progress using progress_reporter callback
    If there is no network connection the packages should already be
    in the apt's cache directory for this command to work.
    If there is network connection apt-get will download the request packages
    by itself if they not present in the cache or the one in the cache
    are outdated.
    The rpm command used to do the job is 'apt-get install'

    Parameters
    ----------
    rpm_fileS : list
    list of rpm packages (not rpm filenames) that need to be installed

    progress_reporter : Callable
    callback function for installation progress reporting

    Returns
    -------
    tuple[bool, str]
    T/F indication installation status, string with reason of failure,
    empty string if success
    """
    package_nameS_string = " ".join(package_nameS)

    progress_reporter.progress_msg("Checking if packages can be installed...")
    status, output = run_shell_command(
        f"apt-get install --reinstall --simulate  {package_nameS_string} -y",
        err_check=False,
    )
    if status:
        regex_install = re.compile(
            r"^(?P<n_upgraded>[0-9]+) upgraded, (?P<n_installed>[0-9]+) newly installed, (?P<n_reinstalled>[0-9]+) reinstalled, (?P<n_removed>[0-9]+) removed and (?P<n_not_upgraded>[0-9]+) not upgraded\.$"
        )
        for line in output.split("\n"):
            if match := regex_install.search(line):
                n_upgraded = match.group("n_upgraded")
                n_installed = match.group("n_installed")
                n_reinstalled = match.group("n_reinstalled")
                n_removed = match.group("n_removed")
                n_not_upgraded = match.group("n_not_upgraded")
                if not (
                    (n_upgraded == n_removed == n_not_upgraded == "0")
                    and n_installed != "0"
                ):
                    msg = (
                        "Dry-run install failed. Packages where not installed: "
                        + output
                    )
                    log.debug(msg)
                    return (False, msg)

    msg = "Dry-run install successful. Proceeding with actual install..."
    log.debug(msg)

    def progress_parser(input: str) -> tuple[str, int]:
        # apt-get reports progress to stdout like this:
        # "  <package name>  ###(changing number of spaces and #) [ 30%]"
        # - 100 % is indicated with 40 # characters
        # - package name != filename (eg. filename=abc.rpm, package name=abc)
        new_regex = re.compile(
            rf"^\s*(?P<p_name>[\w\.\-]+)\s[\s\#]*\[\s*(?P<progress>[0-9]+)%\]$"
        )
        if match := new_regex.search(input):
            return (match.group("p_name"), int(match.group("progress")))
        return ("no match", 0)

    _, output = run_shell_command_with_progress(
        f"apt-get install --reinstall {package_nameS_string} -y",
        progress_reporter=progress_reporter,
        parser=progress_parser,
    )
    if "needs" in output:
        msg = "Installation of rpm packages failed - insufficient disk space. Packages where not installed "
        log.error(msg + output)
        return (False, msg)
    elif "error" in output or "Error" in output:
        msg = "Installation of rpm packages failed. Check logs. "
        log.error(msg + output)
        return (False, msg)
    else:
        msg = "Rpm packages successfully installed. "
        log.debug(msg + output)
        return (True, msg)


def clean_dir(dir_path: pathlib.Path) -> tuple[bool, str]:
    """Removes and recreates a dir to make sure it is empty"""
    try:
        if dir_path.exists():
            shutil.rmtree(dir_path)
        create_dir(dir_path)
        return (True, f"Recreated {dir_path}")
    except Exception as error:
        msg = "Could not recreate directory "
        log.error(msg + str(error))
        return (False, msg)


def extract_tgz(archive_path: pathlib.Path) -> list[pathlib.Path]:
    """Extracts rpm files from LO tar.gz archive to working directory

    Parameters
    ----------
    archive_path : pathlib.Path

    Returns
    -------
    list[pathlib.Path]
      list of absolute paths to extracted rpm files
    """

    target_dir = configuration.working_dir

    # Inspect the archive
    resulting_dir_name = ""
    try:
        with tarfile.open(archive_path) as targz:
            # Assume that it will always be the case
            # that the first name in the archive is the top level
            # directory name to which the rest of the files will be extracted
            resulting_dir_name = targz.getnames()[0]
    except Exception as error:
        log.error(f"Could not inspect archive: {error}")
        return []
    log.debug(f"Top level dir name in the archive: {resulting_dir_name}")
    unpacked_dir = pathlib.Path(target_dir).joinpath(resulting_dir_name)

    # Unpack the archive
    try:
        shutil.unpack_archive(archive_path, target_dir, format="gztar")
        log.debug(f"Was archive extracted?: {unpacked_dir.exists()}")
    except Exception as error:
        log.error(f"Could not extract archive: {error}")
        return []

    # Gather rpm filenames (strings)
    RPMS_dir = unpacked_dir.joinpath("RPMS")
    success, output = run_shell_command("ls " + str(RPMS_dir))
    rpm_files_names = []
    if success:
        for item in output.split():
            rpm_files_names.append(item)
    else:
        log.error(f"Could not list directory contetnt")
        return []

    # Move all files from the unpackaged /target_dir/resulting_dir_name/RPMS
    # directly to /target_dir
    for rpm_file in RPMS_dir.iterdir():
        move_file(from_path=rpm_file, to_path=target_dir)

    # Remove the remanent of unpacked_dir
    try:
        shutil.rmtree(unpacked_dir)
    except Exception as error:
        log.error(f"Could not delete directory: {error}")
        return []

    # Build final list of absolute path to rpm files sitting in target_dir
    rpm_files = []
    for filename in rpm_files_names:
        rpm_files.append(target_dir.joinpath(filename))

    return rpm_files


def install_using_rpm(
    rpm_fileS: list,
    progress_reporter: Callable,
) -> tuple[bool, str]:
    """Install rpm packages using rpm binary installed in the OS

    This function first performs dry-run to check if the list of
    rpm files provided can be installed and if so proceeds with
    actual install reporting progress using progress_reporter callback
    The rpm command used to do the job is 'rpm -Uvh'

    Parameters
    ----------
    rpm_fileS : list
    list of absolute paths to rpm files that need to be installed

    progress_reporter : Callable
    callback function for installation progress reporting

    Returns
    -------
    tuple[bool, str]
    T/F indication installation status, string with reason of failure,
    empty string if success
    """

    files_to_install = " ".join([str(rpm_path) for rpm_path in rpm_fileS])

    progress_reporter.progress_msg("Checking if packages can be installed...")
    status, output = run_shell_command(
        "rpm -Uvh --replacepkgs --test " + files_to_install,
        err_check=False,
    )
    if status:
        if "needs" in output:
            msg = "Dry-run install failed - insufficient disk space. Packages where not installed "
            log.error(msg + output)
            return (False, msg)
        if any(map(lambda e: e in output, ["error", "Error"])):
            msg = "Dry-run install failed. Packages where not installed "
            log.error(msg + output)
            return (False, msg)
        else:
            msg = "Dry-run install successful. Proceeding with actual install..."
            log.debug(msg)

            # It seems rpm is manipulating TTY directly :(
            # Although TTY can be captured the method below relies
            # on '#' symbols being written to stdout when rpm is making
            # progress installing rpm. Counting them to calculate percentage.
            def progress_parser(input: bytes) -> tuple[str, int]:
                # regex for stdout output
                regex_verifying = re.compile(r"Verifying[\.]+\s*(?P<p_progress>[\#]+)")
                regex_preparing = re.compile(r"Preparing[\.]+\s*(?P<p_progress>[\#]+)")
                regex_updinst = re.compile(r"Updating\s/\sinstalling[\.]+")
                regex_name_and_progress = re.compile(
                    r"^[\s0-9]+\:[\s]+(?P<p_name>[\w\.\-]+)\s*(?P<p_progress>[\#]+)"
                )
                last_string = input.decode("utf-8").split("\n")[-1]
                # Unfortunately rpm outputs backspace control chars
                # to do its progress reporting which
                # means some long rpm names can get trimmed.
                # To try to deal with that we save the name the first time
                # regex match is successful and we retain it (and return it)
                # until we gather max no of '#' symbols (should be 40 but is 33)
                # then we reset for next package name.
                hashes4done = 33
                first = True
                p_name = ""
                p_progress = 0
                match_verifying = regex_verifying.search(last_string)
                match_preparing = regex_preparing.search(last_string)
                match_updinst = regex_updinst.search(last_string)
                match_n_p = regex_name_and_progress.search(last_string)
                if match_verifying:
                    verifying_msg = "Verifying..."
                    p_progress = int(
                        100 * len(match_verifying.group("p_progress")) / hashes4done
                    )
                    return (verifying_msg, p_progress)
                elif match_preparing:
                    preparing_msg = "Preparing..."
                    p_progress = int(
                        100 * len(match_preparing.group("p_progress")) / hashes4done
                    )
                    return (preparing_msg, p_progress)
                elif match_updinst:
                    installing_msg = "Installing..."
                    p_progress = 0
                    return (installing_msg, p_progress)
                elif match_n_p:
                    if first:
                        p_name = match_n_p.group("p_name")
                        p_progress = int(
                            100 * len(match_n_p.group("p_progress")) / hashes4done
                        )
                        first = False
                    else:
                        p_progress = int(
                            100 * len(match_n_p.group("p_progress")) / hashes4done
                        )
                        if len(match_n_p.group("p_progress")) == hashes4done:
                            first = True
                    return (p_name, p_progress)
                else:
                    return ("no match", 0)

            status, msg = run_shell_command_with_progress(
                f"rpm -Uvh --replacepkgs {files_to_install}",
                progress_reporter=progress_reporter,
                parser=progress_parser,
                byte_output=True,
            )
            log.debug(f"final msg is: {msg}")
            if "error" in msg:
                return (False, "Failed to install packages")
            else:
                return (True, "All packages successfully installed")
    else:
        msg = "Failed to execute command: " + output
        log.debug(msg)
        return (False, msg)


def uninstall_using_apt_get(
    package_nameS: list,
    progress_reporter: Callable,
):
    """Uninstalls rpm packages using apt-get command provided by the OS

    This function first performs dry-run to check if the list of
    rpm files provided can be removed without conflicts
    and if so proceeds with actual uninstall reporting progress
    using progress_reporter callback
    The command used to do the job is 'apt-get remove'

    Parameters
    ----------
    rpm_fileS : list
    list rpm packages (not rpm filenames) need to be removed

    progress_reporter : Callable
    callback function for installation progress reporting

    Returns
    -------
    tuple[bool, str]
    T/F indication status status, string with reason of failure,
    empty string if success
    """
    package_nameS_string = " ".join(package_nameS)

    progress_reporter.progress_msg("Checking if packages can be uninstalled...")
    status, output = run_shell_command(
        f"apt-get remove --simulate  {package_nameS_string} -y",
        err_check=False,
    )
    if status:
        regex_install = re.compile(
            r"^(?P<n_upgraded>[0-9]+) upgraded, (?P<n_installed>[0-9]+) newly installed, (?P<n_removed>[0-9]+) removed and (?P<n_not_upgraded>[0-9]+) not upgraded\.$"
        )
        for line in output.split("\n"):
            if match := regex_install.search(line):
                # Out should contain a line:
                # "0 upgraded, 0 newly installed, X removed and Y not upgraded."
                # where X must be != 0, Y doesn't matter, can be anything
                n_upgraded = match.group("n_upgraded")
                n_installed = match.group("n_installed")
                n_removed = match.group("n_removed")
                n_not_upgraded = match.group("n_not_upgraded")
                if not ((n_upgraded == n_installed == "0") and n_removed != "0"):
                    msg = (
                        "Dry-run removal failed. Packages where not removed: " + output
                    )
                    log.debug(msg)
                    return (False, msg)

    msg = "Dry-run removal successful. Proceeding with actual uninstall..."
    log.debug(msg)

    def progress_parser(input: str) -> tuple[str, int]:
        # apt-get reports progress to stdout like this:
        # "  <package name>  ###(changing number of spaces and #) [ 30%]"
        # - 100 % is indicated with 40 # characters
        # - package name != filename (eg. filename=abc.rpm, package name=abc)
        new_regex = re.compile(
            rf"^\s*(?P<p_name>[\w\.\-]+)\s[\s\#]*\[\s*(?P<progress>[0-9]+)%\]$"
        )
        if match := new_regex.search(input):
            return (match.group("p_name"), int(match.group("progress")))
        return ("no match", 0)

    _, msg = run_shell_command_with_progress(
        f"apt-get remove {package_nameS_string} -y",
        progress_reporter=progress_reporter,
        parser=progress_parser,
    )
    if "error" in msg or "Error" in msg:
        return (False, "Removal of rpm packages failed. Check logs.")
    else:
        return (True, "Rpm packages successfully removed.")


def force_rm_directory(path: pathlib.Path):
    try:
        if path.exists():
            shutil.rmtree(path)
    except Exception as error:
        log.error("Failed to remove directory" + str(error))


def update_menus():
    """Updates KDE/GNOME/LXDE etc. menus"""
    log.info("updating menus")
    run_shell_command("xdg-desktop-menu forceupdate --mode system", err_check=False)
    run_shell_command("update-menus -n", err_check=False)
    run_shell_command("update-menus -v", err_check=False)


def make_dir_tree(target_dir: pathlib.Path):
    """Recursivly create directories needed to contain the leaf directory"""
    os.makedirs(target_dir, exist_ok=True)
