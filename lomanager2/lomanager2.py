import argparse
from adapters import qt_adapter, cli_adapter
import configuration

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

is_running_as_root = True  # TODO: Implement checking

is_GUI_wanted = args.gui
# TODO: affect logging level directly
is_DEBUG_mode_on = args.debug
keep_logging_messages_in_english = args.force_english_logs

# TODO: prints for test purposes, remove when not needed
configuration.logging.debug(f"is_GUI_wanted: {is_GUI_wanted}")
configuration.logging.debug(f"is_DEBUG_mode_on {is_DEBUG_mode_on}")
configuration.logging.debug(f"keep_logging_messages_in_english: {keep_logging_messages_in_english}")

if is_running_as_root:
    if is_GUI_wanted is True:
        qt_adapter.main()
    else:
        cli_adapter.main()
else:
    print("This program requires root privileges to run.")
