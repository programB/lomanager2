import gettext
import hashlib
import logging
import pathlib
import socket
import time
import urllib.error
import urllib.request
from typing import Callable


t = gettext.translation("lomanager2", localedir="./locales", fallback=True)
_ = t.gettext
log = logging.getLogger("lomanager2_logger")

connections_timeout = 15
# Needed for urlretrieve
socket.setdefaulttimeout(connections_timeout)


def check_url_available(url: str) -> tuple[bool, str]:
    try:
        resp = urllib.request.urlopen(url, timeout=connections_timeout)
        log.debug(_("Resource available: {}").format(url))
        return (True, resp)
    except urllib.error.HTTPError as error:
        msg = _("While trying to open {} an error occurred: ").format(url)
        msg = msg + _("HTTP error {}: {}").format(error.code, error.reason)
        return (False, msg)
    except urllib.error.URLError as error:
        msg = _("While trying to open {} an error occurred: ").format(url)
        msg = msg + f"{error.reason}"
        return (False, msg)


def download_file(
    src_url: str,
    dest_path: pathlib.Path,
    progress_reporter: Callable,
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
            progress_reporter.progress(percent_p)

    filename = src_url.split("/")[-1]
    progress_reporter.progress_msg(_("Downloading: {}").format(filename))

    for attempt in range(1, max_retries + 1):
        try:
            urllib.request.urlretrieve(
                src_url,
                filename=dest_path,
                reporthook=progress_reporthook,
            )
            progress_reporter.progress_msg(_("Downloaded:      {}").format(filename))
            return (True, "")
        except Exception as error:
            log.error(_("Attempt {} of {} failed").format(attempt, max_retries))
            log.error(error)
            info = str(error)
            time.sleep(retry_delay_sec)
    info = _("Failed to download file. ") + info
    return (False, info)


def verify_checksum(
    file: pathlib.Path,
    checksum_file: pathlib.Path,
    progress_reporter: Callable,
) -> bool:
    progress_reporter.progress_msg(_("Verifying:       {}").format(file.name))

    with open(file, "rb") as f:
        file_tot_size = file.stat().st_size
        chunk_size = 8192
        steps = int(file_tot_size / chunk_size) + 2
        i = 0
        file_hash = hashlib.md5()
        while chunk := f.read(chunk_size):
            file_hash.update(chunk)
            progress_p = int((i / (steps)) * 100)
            progress_reporter.progress(progress_p)
            i += 1

    calculated_hash = file_hash.hexdigest()

    with open(checksum_file, "r") as fmd:
        lines = fmd.readlines()
    checksum = lines[0].split()[0]  # first word in the first line

    if is_correct := calculated_hash == checksum:
        progress_reporter.progress_msg(_("hash OK:         {}").format(file.name))
    return is_correct
