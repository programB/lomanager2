import logging
import pathlib

lomanger2_version = "7.5"
latest_available_LO_version = "7.5"
latest_available_clipart_version = "5.8"

logging.basicConfig(
    format="[%(levelname)s](%(asctime)s) (in %(module)s.%(funcName)s): %(message)s",
    level=logging.DEBUG,
)

# Only every set tmp_directory in this module
tmp_directory = pathlib.Path("/tmp/lomanager2-tmp")
