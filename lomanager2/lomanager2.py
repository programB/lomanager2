import argparse

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
is_DEBUG_mode_on = args.debug
keep_logging_messages_in_english = args.force_english_logs

# TODO: prints for test purposes, remove when not needed
print(f"is_GUI_wanted: {is_GUI_wanted}")
print(f"is_DEBUG_mode_on {is_DEBUG_mode_on}")
print(f"keep_logging_messages_in_english: {keep_logging_messages_in_english}")

if is_running_as_root:
    if is_GUI_wanted is True:
        # TODO: Implement
        print("Running with GUI ... ")
    else:
        # TODO: Implement
        print("Running with CLI ... ")
else:
    print("This program requires root privileges to run.")
