"""
Copyright (C) 2023 programB

This file is part of lomanager2.

lomanager2 is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License version 3
as published by the Free Software Foundation.

lomanager2 is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with lomanager2.  If not, see <http://www.gnu.org/licenses/>.
"""
import argparse
import logging
import os
from datetime import datetime

from i18n import _

parser = argparse.ArgumentParser(description=_("Run lomanager2"))
parser.add_argument(
    "--cli", action="store_true", help=_("use command line interface (no GUI)")
)
parser.add_argument("--debug", action="store_true", help=_("run in debug mode"))
parser.add_argument(
    "--skip-update-check",
    action="store_true",
    help=_(
        "skips checking OS update status. Only works with --debug flag. "
        "Installing packages in this mode can potentially mess up your "
        "system! Use at your own risk."
    ),
)
args = parser.parse_args()


# Check if programs runs with root privileges
if os.geteuid() == 0:
    # Setup logging
    # Create log(s) directory
    logs_dir = "/root/.lomanager2/log/"
    os.makedirs(logs_dir, exist_ok=True)

    logger = logging.getLogger("lomanager2_logger")
    logger.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if args.debug else logging.WARNING)

    log_filename = datetime.now().strftime("%Y-%m-%d_%H%M%S") + ".log"
    logfile_handler = logging.FileHandler(
        logs_dir + log_filename, mode="w", encoding="utf-8", delay=False, errors=None
    )
    logfile_handler.setLevel(logging.DEBUG if args.debug else logging.INFO)

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
    logger.info(_("Log started"))
    if args.cli is True:
        from adapters import cli_adapter

        cli_adapter.main(skip_update_check=args.debug and args.skip_update_check)
    else:
        from adapters import qt_adapter

        qt_adapter.main(skip_update_check=args.debug and args.skip_update_check)
else:
    print(_("This program requires root privileges to run."))
