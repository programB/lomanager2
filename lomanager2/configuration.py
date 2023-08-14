import logging
import pathlib

logging.basicConfig(
    format="[%(levelname)s](%(asctime)s) (in %(module)s.%(funcName)s): %(message)s",
    level=logging.DEBUG,
)

lomanger2_version = "7.5"
# latest_available_LO_version = "7.5"
latest_available_LO_version = "7.5.4.2"
latest_available_LO_minor_version = "7.5.4"
latest_available_clipart_version = "7.5"
# latest_available_java_version = "16"
latest_available_java_version = ""
# fmt: off
# LO_supported_langs = ["af","am","ar","as","ast",
#                       "be","bg","bn-IN","bn","bo","br","brx","bs",
#                       "ca-valencia","ca","ckb","cs","cy",
#                       "da","de","dgo","dsb","dz",
#                       "el","en-GB","en-ZA","eo","es","et","eu",
#                       "fa","fi","fr","fur","fy",
#                       "ga","gd","gl","gu","gug",
#                       "he","hi","hr","hsb","hu",
#                       "id","is","it",
#                       "ja",
#                       "ka","kab","kk","km","kmr-Latn","kn","ko","kok","ks",
#                       "lb","lo","lt","lv",
#                       "mai","mk","ml","mn","mni","mr","my",
#                       "nb","ne","nl","nn","nr","nso",
#                       "oc","om","or",
#                       "pa-IN","pl","pt-BR","pt",
#                       "ro","ru","rw",
#                       "sa-IN","sat","sd","si","sid","sk","sl","sq","sr-Latn",
#                       "sr","ss","st","sv","sw-TZ","szl",
#                       "ta","te","tg","th","tn","tr","ts","tt",
#                       "ug","uk","uz",
#                       "ve","vec","vi",
#                       "xh",
#                       "zh-CN","zh-TW","zu"]
# fmt: on
logging.debug("Supported language set limited for tests")
LO_supported_langs = ["de", "fr", "it", "ja", "pl", "sk", "sv", "uk", "xh"]


# Only every set tmp_directory in this module
tmp_directory = pathlib.Path("/tmp/lomanager2-tmp")
download_dir = pathlib.Path("/tmp")
working_dir = pathlib.Path("/tmp/lomanager2-tmp/working_directory")
verified_dir = pathlib.Path("/tmp/lomanager2-tmp/verified_storage")

# Read only
keep_packages = False

# Urls
PCLOS_repo_base_url = "https://ftp.nluug.nl/"
PCLOS_repo_path = "/os/Linux/distr/pclinuxos/pclinuxos/apt/pclinuxos/64bit/RPMS.x86_64/"
DocFund_base_url = "http://download.documentfoundation.org/libreoffice/stable/"
DocFund_path_ending = "/rpm/x86_64/"

