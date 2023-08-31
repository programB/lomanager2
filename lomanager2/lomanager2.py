import os
from datetime import datetime
import argparse
import logging


parser = argparse.ArgumentParser(description="Run lomanager2")
parser.add_argument("--gui", action="store_true", help="run with GUI")
parser.add_argument("--debug", action="store_true", help="run in debug mode")
parser.add_argument(
    "--force_english_logs",
    action="store_true",
    help="ignores locale setting for loggig purposes and uses hardcoded "
    "strings instead. Note that the interface will still be localized.",
)
args = parser.parse_args()


# Check if programs runs with root privileges
if os.geteuid() == 0:
    keep_logging_messages_in_english = args.force_english_logs

    # Setup logging
    log_level = logging.DEBUG if args.debug else logging.INFO

    # Create log(s) folder
    logs_path = "/root/.lomanager2/log/"
    os.makedirs(logs_path, exist_ok=True)

    logger = logging.getLogger("lomanager2_logger")
    logger.setLevel(log_level)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)

    log_filename = datetime.now().strftime("%Y-%m-%d_%H%M%S") + ".log"
    logfile_handler = logging.FileHandler(
        logs_path + log_filename, mode="w", encoding="utf-8", delay=False, errors=None
    )
    logfile_handler.setLevel(log_level)

    debug_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] (in %(module)s.%(funcName)s): %(message)s"
    )
    normal_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    formatter = debug_formatter if args.debug else normal_formatter
    console_handler.setFormatter(formatter)
    logfile_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(logfile_handler)

    # Run the app with chosen interface
    if args.gui is True:
        from adapters import qt_adapter

        qt_adapter.main()
    else:
        from adapters import cli_adapter

        cli_adapter.main()
else:
    print("This program requires root privileges to run.")
