"""
This module gathers functions to get or set operating system state.
Functions that use basic operations on the operating system either
to get information or to cause some changes in the operating system
and this by directly calling external, system program or by methods
from python standard library.
These are service providing functions, not procedures in app's logic.

These functions must not not hold any state (or be made to hold it
by turning them into closures or classes) - they should get the information
directly from the system on each call.
"""


import time
import os
import shutil
import pathlib
from typing import Callable
from configuration import logging as log
import configuration
import urllib.request, urllib.error
import hashlib
import subprocess
import re
import tarfile
import pwd


def has_root_privileges() -> bool:
    return os.geteuid == 0


def run_shell_command(
    cmd: str, shell="bash", timeout=1, err_check=True
) -> tuple[bool, str]:
    if cmd:
        full_command = [shell] + ["-c"] + [cmd]
        log.debug(f"Attempting to execute command: {full_command}")

        try:
            shellcommand = subprocess.run(
                full_command,
                check=err_check,  # some commads return non-zero exit code if successful
                timeout=timeout,  # fail on command taking to long to exec.
                capture_output=True,  # capture output (both stdout and stderr)
                text=True,  # give the output as a string not bytes
                encoding="utf-8",  # explicitly set the encoding for the text
            )
            answer = (shellcommand.stdout + shellcommand.stderr).strip()
            if err_check:
                log.debug(
                    f"(error checking is ON) Received answer (stdout+stderr): {answer}"
                )
            else:
                log.debug(
                    f"(error checking is OFF) Received answer (stdout+stderr): {answer}"
                )
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
    package_managers = [
        "synaptic",
        "smart",
        "ksmarttray",
        "kpackage",
        "apt-get",
    ]
    running_managers = {}
    returned_pids = get_PIDs_by_name(package_managers)
    is_succesful = True if not "Error" in returned_pids.keys() else False
    if is_succesful:
        for key, item in returned_pids.items():
            if item:
                running_managers[key] = ", ".join(item)
    log.debug(f"running managers: {running_managers}")
    return (is_succesful, running_managers)


def get_running_Office_processes() -> tuple[bool, dict]:
    binaries_to_check = ["soffice.bin"]
    running_office_suits = {}
    returned_pids = get_PIDs_by_name(binaries_to_check)
    is_succesful = True if not "Error" in running_office_suits.keys() else False
    if is_succesful:
        for key, item in returned_pids.items():
            if item:
                log.debug(f"ITEM: {item}, {type(item)}")
                running_office_suits[key] = ", ".join(item)
    return (is_succesful, running_office_suits)


class HumanUser:
    def __init__(self, name, home_dir) -> None:
        self.name = name
        self.home_dir = pathlib.Path(home_dir)


def get_system_users() -> list[HumanUser]:
    """Looks for regular (not services) system users.

    The criteria are that the user has a login shell that is one
    of the shells listed in /etc/shells and has a home folder in /home.
    Additioanly root user is included.
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
    # TODO: Verify implementation
    return pathlib.Path("/union").exists()


def check_system_update_status() -> tuple[bool, bool, str]:
    # Update package index
    # Since the apt-get update command fetches data from
    # repo server it make take a while hence setting timeout to 45 sek.
    status, output = run_shell_command("apt-get update", timeout=45, err_check=False)
    if status:
        status, output = run_shell_command(
            "apt-get dist-upgrade --fix-broken --simulate", timeout=15, err_check=True
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


def is_lomanager2_latest(lomanger2_version: str) -> bool:
    # TODO: Implement
    return True


def free_space_in_dir(dir: pathlib.Path) -> int:
    """Return free disk space for the partition holding dir.

    Returns
    -------
    free_space : int
        Free space in kibibytes (KiB).
    """

    free_space = int(shutil.disk_usage(dir).free / 1024)
    log.debug(f"free space in {dir}: {free_space} KiB")
    return free_space


def detect_installed_java() -> tuple[bool, str]:
    found = pathlib.Path("/usr/bin/java").exists()
    # Since this program is not meant to update Java,
    # Java version is not being detected.
    java_version = ""
    log.debug(f"Is Java installed?: {found}")
    return (found, java_version)


def detect_installed_office_software() -> list[tuple[str, str, tuple]]:
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
    for version in configuration.LO_versionS:
        if pathlib.Path("/usr/bin/libreoffice" + version).exists():
            dbg_message = ("Detected LibreOffice ver.: {}").format(version)
            log.debug(dbg_message)

            # Try to detect language packs installed but only for
            # for series 7.0 and above
            if int(version.split(".")[0]) < 7:
                list_of_detected_suits.append(("LibreOffice", version, ()))
            else:
                success, reply = run_shell_command(
                    f"rpm -qa | grep libreoffice{version}", err_check=False
                )
                if success and reply:
                    regex_lang = re.compile(
                        rf"^libreoffice{version}-(?P<det_lang>[a-z][a-z])(?P<det_regio>\-[a-z]*[A-Z]*[A-Z]*)?-{version}[0-9\-\.]*[0-9]$"
                    )
                    # example matches:
                    # libreoffice7.5-fr-7.5.4.2-2
                    # #  det_lang = "fr" det_regio = ""
                    # libreoffice7.4-ca-valencia-7.4.4.2-2
                    # #  det_lang = "ca" det_regio = "-valencia"
                    # libreoffice7.4-en-GB-7.4.4.2-2
                    # #  det_lang = "en" det_regio = "-GB"
                    langs_found = []
                    for package in reply.split("\n"):
                        if match := regex_lang.search(package):
                            det_lang = match.group("det_lang")
                            det_regio = match.group("det_regio")
                            if det_regio:
                                det_lang = det_lang + det_regio
                            langs_found.append(det_lang)
                    list_of_detected_suits.append(
                        (
                            "LibreOffice",
                            version,
                            tuple(langs_found),
                        )
                    )
                else:
                    list_of_detected_suits.append(("LibreOffice", version, ()))

    inf_message = ("All detected office suits (and langs): {}").format(
        list_of_detected_suits
    )
    log.info(inf_message)
    return list_of_detected_suits


def detect_installed_clipart() -> tuple[bool, str]:
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


def download_file(
    src_url: str,
    dest_path: pathlib.Path,
    progress: Callable,
    progress_description: Callable,
    max_retries: int = 3,
    retry_delay_sec: int = 5,
) -> tuple[bool, str]:
    info = ""

    def progress_reporthook(n_blocks_transferred, block_size, file_tot_size):
        already_got_bytes = n_blocks_transferred * block_size
        if file_tot_size == -1:
            pass
        else:
            percent_p = int(100 * (already_got_bytes / file_tot_size))
            progress(percent_p)

    filename = src_url.split("/")[-1]
    progress_description(f"Now downloading: {filename}")

    for attempt in range(1, max_retries + 1):
        try:
            urllib.request.urlretrieve(
                src_url,
                filename=dest_path,
                reporthook=progress_reporthook,
            )
            progress_description(f"Downloaded:      {filename}")
            return (True, "")
        except Exception as error:
            log.error(f"Attempt {attempt} of {max_retries} failed")
            log.error(error)
            info = str(error)
            time.sleep(retry_delay_sec)
    info = "Failed to download file. " + info
    return (True, info)


def verify_checksum(
    file: pathlib.Path,
    checksum_file: pathlib.Path,
    progress: Callable,
    progress_description: Callable,
) -> bool:
    progress_description(f"Verifying:       {file.name}")

    with open(file, "rb") as f:
        file_tot_size = file.stat().st_size
        chunk_size = 8192
        steps = int(file_tot_size / chunk_size) + 2
        i = 0
        file_hash = hashlib.md5()
        while chunk := f.read(chunk_size):
            file_hash.update(chunk)
            progress_p = int((i / (steps)) * 100)
            progress(progress_p)
            i += 1

    calculated_hash = file_hash.hexdigest()

    with open(checksum_file, "r") as fmd:
        lines = fmd.readlines()
    checksum = lines[0].split()[0]  # first word in the first line

    if is_correct := calculated_hash == checksum:
        progress_description(f"hash OK:         {file.name}")
    return is_correct


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


def create_directories():
    directories = [
        configuration.working_dir,
        configuration.verified_dir.joinpath("Java_rpms"),
        configuration.verified_dir.joinpath("LibreOffice-core_tgzs"),
        configuration.verified_dir.joinpath("LibreOffice-langs_tgzs"),
        configuration.verified_dir.joinpath("Clipart_rpms"),
    ]
    for directory in directories:
        log.debug(f"Creating: {directory}")
        os.makedirs(directory, exist_ok=True)


def run_shell_command_with_progress(
    cmd,
    progress: Callable,
    progress_description: Callable,
    parser: Callable,
    byte_output=False,
) -> tuple[bool, str]:
    full_command = cmd
    fulloutput = []
    ctrl_chars = list(map(chr, range(0, 32))) + list(map(chr, range(127, 160)))

    with subprocess.Popen(
        full_command,
        bufsize=1,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=False,
        universal_newlines=not byte_output,
    ) as proc:
        concatenated_b = b""
        while proc.poll() is None:
            if byte_output:
                output = proc.stdout.read(1)
                concatenated_b += output
                fulloutput.append(output.decode("utf-8"))
            else:  # strings
                output = proc.stdout.readline()
                fulloutput.append(output)
            if parser:
                if byte_output:
                    string_to_parse = concatenated_b
                    # Don't bother reporting progress and spamming
                    # log if only a control char was read
                    if output.decode("utf-8") not in ctrl_chars:
                        label, percentage = parser(string_to_parse)
                        progress_description(label)
                        progress(percentage)
                    else:
                        pass
                else:
                    string_to_parse = output
                    label, percentage = parser(string_to_parse)
                    progress_description(label)
                    progress(percentage)
    return (True, "".join(fulloutput))


def install_using_apt_get(
    package_nameS: list,
    progress_description: Callable,
    progress_percentage: Callable,
):
    #   apt-get reports install progress to stdout like this:
    # "  <packages_name>  ###(changing numeber of spaces and #) [ 30%]"
    #   Build some reg. expressions to capture this
    # NOTE: package_name != filename (filename=abc.rpm, package_name=abc)
    regeXs = []
    for p_name in package_nameS:
        regeXs.append(
            re.compile(rf"^\s*(?P<p_name>{p_name})[\s\#]*\[\s*(?P<progress>[0-9]+)%\]$")
        )

    def progress_parser(input: str) -> tuple[str, int]:
        for regex in regeXs:
            if match := regex.search(input):
                return (match.group("p_name"), int(match.group("progress")))
        return ("", 0)

    run_shell_command_with_progress(
        ["apt-get install --reinstall task-java -y"],
        progress=progress_percentage,
        progress_description=progress_description,
        parser=progress_parser,
    )


def clean_working_dir() -> bool:
    # remove and recreate working_dir to make sure it is empty
    target_dir = configuration.working_dir
    try:
        shutil.rmtree(target_dir)
        os.makedirs(target_dir, exist_ok=False)
        return True
    except Exception as error:
        log.error(f"Could not recreate working directory: {error}")
        return False


def extract_tgz(archive_path: pathlib.Path) -> list[pathlib.Path]:
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
    unpacked_folder = pathlib.Path(target_dir).joinpath(resulting_dir_name)

    # Unpack the archive
    try:
        shutil.unpack_archive(archive_path, target_dir, format="gztar")
        log.debug(f"Was archive extracted?: {unpacked_folder.exists()}")
    except Exception as error:
        log.error(f"Could not extract archive: {error}")
        return []

    # Gather rpm filenames (strings)
    RPMS_folder = unpacked_folder.joinpath("RPMS")
    success, output = run_shell_command("ls " + str(RPMS_folder))
    rpm_files_names = []
    if success:
        for item in output.split():
            rpm_files_names.append(item)
    else:
        log.error(f"Could not list directory contetnt")
        return []

    # Move all files from the unpackaged /target_dir/resulting_dir_name/RPMS
    # directly to /target_dir
    for rpm_file in RPMS_folder.iterdir():
        move_file(from_path=rpm_file, to_path=target_dir)

    # Remove the remanent of unpacked_folder
    try:
        shutil.rmtree(unpacked_folder)
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
    progress_description: Callable,
    progress_percentage: Callable,
) -> tuple[bool, str]:
    files_to_install = " ".join([str(rpm_path) for rpm_path in rpm_fileS])

    # Before going ahead with actual installation, test for potential problems
    log.debug("Trying dry-run install to check for errors...")
    status, output = run_shell_command(
        "rpm -Uvh --test " + files_to_install,
        timeout=5,
        err_check=False,
    )
    if status:
        if "error" in output:
            msg = "Dry-run install failed. Packages where not installed: " + output
            log.debug(msg)
            return (False, msg)
        else:
            msg = "Dry-run install successful. Proceeding with actual install..."
            log.debug(msg)

            # It seems rpm is manipulating TTY directly :(
            # Although TTY can be captured the method below relies
            # on up 40 # symbols being written to stodout when rpm is making
            # progress installing rpm. Counting them to calculate percentage.
            def progress_parser(input: bytes) -> tuple[str, int]:
                # regex for stdout output
                regex_name_and_progress = re.compile(
                    r"^(?P<p_name>[\w\.\-]+)\s*(?P<p_progress>[\#]+)"
                )
                last_string = input.decode("utf-8").split("\n")[-1]
                # Unfortunately rpm outputs 40 backspace control chars
                # to do its progress reporting which
                # means some long rpm names can get trimmed.
                # To try to deal with that we save the name the first time
                # regex match is successful and we retain it (and return it)
                # until we gather 40 # symbols then we reset for next
                # package name.
                first = True
                p_name = ""
                p_progress = 0
                if match := regex_name_and_progress.search(last_string):
                    # log.debug("match found")
                    if first:
                        p_name = match.group("p_name")
                        p_progress = int(100 * len(match.group("p_progress")) / 40)
                        first = False
                    else:
                        p_progress = int(100 * len(match.group("p_progress")) / 40)
                        if len(match.group("p_progress")) == 40:
                            first = True
                    return (p_name, p_progress)
                else:
                    if last_string == b"":
                        return ("", 0)
                    else:
                        return ("Working...", 0)

            cmd_list = ["bash", "-c"]
            rpm_cmd = ["rpm -Uvh " + files_to_install]
            status, msg = run_shell_command_with_progress(
                cmd_list + rpm_cmd,
                # Example
                # [
                #     "bash",
                #     "-c",
                #     "rpm -Uvh /tmp/lomanager2-tmp/working_directory/tanglet-1.6.1.1-1pclos2022.x86_64.rpm",
                # ],
                progress=progress_percentage,
                progress_description=progress_description,
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
    progress_description: Callable,
    progress_percentage: Callable,
):
    package_nameS_string = " ".join(package_nameS)
    #   apt-get reports install progress to stdout like this:
    # "  <package_name>  ###(changing numeber of spaces and #) [ 30%]"
    # NOTE: package_name != filename (filename=abc.rpm, package_name=abc)
    new_regex = re.compile(
        rf"^\s*(?P<p_name>[\w\.\-]+)\s[\s\#]*\[\s*(?P<progress>[0-9]+)%\]$"
    )

    def progress_parser(input: str) -> tuple[str, int]:
        if match := new_regex.search(input):
            return (match.group("p_name"), int(match.group("progress")))
        return ("", 0)

    _, msg = run_shell_command_with_progress(
        ["bash", "-c", f"apt-get remove {package_nameS_string} -y"],
        progress=progress_percentage,
        progress_description=progress_description,
        parser=progress_parser,
    )
    if "error" in msg or "Error" in msg:
        return (False, "Removal of rpm packages failed. Check logs.")
    else:
        return (True, "Rpm packages successfully removed.")


def force_rm_directory(path):
    try:
        shutil.rmtree(path)
    except Exception as error:
        log.error("Failed to remove folder" + str(error))


def update_menus():
    log.debug("updating menus")
    run_shell_command("update-menus -v")


def make_dir_tree(target_dir: pathlib.Path):
    os.makedirs(target_dir, exist_ok=True)
