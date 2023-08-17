import logging
import pathlib
import socket

socket.setdefaulttimeout(15)

logging.basicConfig(
    format="[%(levelname)s](%(asctime)s) (in %(module)s.%(funcName)s): %(message)s",
    level=logging.DEBUG,
)

lomanger2_version = "7.5"
# latest_available_LO_version = "7.5"
latest_available_LO_version = "7.5.4.2"
force_specific_LO_version = "7.3.6.3"
latest_available_clipart_version = "7.5"
# latest_available_java_version = "16"
latest_available_java_version = ""


# Only every set actual directories names in this module
working_dir = pathlib.Path("/tmp/lomanager2-tmp/working_directory")
verified_dir = pathlib.Path("/tmp/lomanager2-tmp/verified_storage")
offline_copy_dir = pathlib.Path("/tmp/lomanager2-saved_packages")

# Read only
keep_packages = False

# Urls
PCLOS_repo_base_url = "https://ftp.nluug.nl/"
PCLOS_repo_path = "/os/Linux/distr/pclinuxos/pclinuxos/apt/pclinuxos/64bit/RPMS.x86_64/"
DocFund_base_url = "http://download.documentfoundation.org/libreoffice/stable/"
DocFund_path_ending = "/rpm/x86_64/"

