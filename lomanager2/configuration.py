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
