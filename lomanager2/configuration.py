import logging
import pathlib

log = logging.getLogger("lomanager2_logger")


latest_available_LO_version = "7.5.4.2"
# force_specific_LO_version = "7.3.6.3"
force_specific_LO_version = ""
latest_available_clipart_version = "7.5"


# Global read-only definitions
working_dir = pathlib.Path("/tmp/lomanager2-tmp/working_directory")
verified_dir = pathlib.Path("/tmp/lomanager2-tmp/verified_storage")
offline_copy_dir = pathlib.Path("/tmp/lomanager2-saved_packages")

# URLs
PCLOS_repo_base_url = "https://ftp.nluug.nl/"
PCLOS_repo_path = "/os/Linux/distr/pclinuxos/pclinuxos/apt/pclinuxos/64bit/RPMS.x86_64/"
DocFund_base_url = "http://download.documentfoundation.org/libreoffice/stable/"
DocFund_path_ending = "/rpm/x86_64/"


def make_base_ver(full_version: str) -> str:
    # base version comprises of the first 2 numbers of the full version
    # eg. 7.5.4.2 -> 7.5
    return ".".join(full_version.split(".")[:2])


def make_minor_ver(full_version: str) -> str:
    # minor version comprises of the first 3 numbers of the full version
    # eg. 7.5.4.2 -> 7.5.4
    return ".".join(full_version.split(".")[:3])
