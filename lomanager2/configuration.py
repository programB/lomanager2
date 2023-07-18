import logging
import pathlib

lomanger2_version = "7.5"
latest_available_LO_version = "7.5"
latest_available_clipart_version = "5.8"
latest_available_java_version = "16"
# fmt: off
LO_supported_langs = ["af","am","ar","as","ast",
                      "be","bg","bn-IN","bn","bo","br","brx","bs",
                      "ca-valencia","ca","ckb","cs","cy",
                      "da","de","dgo","dsb","dz",
                      "el","en-GB","en-ZA","eo","es","et","eu",
                      "fa","fi","fr","fur","fy",
                      "ga","gd","gl","gu","gug",
                      "he","hi","hr","hsb","hu",
                      "id","is","it",
                      "ja",
                      "ka","kab","kk","km","kmr-Latn","kn","ko","kok","ks",
                      "lb","lo","lt","lv",
                      "mai","mk","ml","mn","mni","mr","my",
                      "nb","ne","nl","nn","nr","nso",
                      "oc","om","or",
                      "pa-IN","pl","pt-BR","pt",
                      "ro","ru","rw",
                      "sa-IN","sat","sd","si","sid","sk","sl","sq","sr-Latn",
                      "sr","ss","st","sv","sw-TZ","szl",
                      "ta","te","tg","th","tn","tr","ts","tt",
                      "ug","uk","uz",
                      "ve","vec","vi",
                      "xh",
                      "zh-CN","zh-TW","zu"]
# fmt: on

logging.basicConfig(
    format="[%(levelname)s](%(asctime)s) (in %(module)s.%(funcName)s): %(message)s",
    level=logging.DEBUG,
)

# Only every set tmp_directory in this module
tmp_directory = pathlib.Path("/tmp/lomanager2-tmp")

# Read only
keep_packages = False
