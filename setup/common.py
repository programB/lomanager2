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
import pathlib

setup_dir = pathlib.Path("setup")
if not setup_dir.is_dir():
    print("This script must be called from the top level directory")
    exit(1)
src_dir = pathlib.Path("lomanager2")

version = ""
package = ""
with open(src_dir.joinpath("defs.py"), "r") as defs_f:
    for line in defs_f:
        if line.startswith("__package__"):
            package = line.split("=")[1].strip().replace("\"","")
        if line.startswith("__version__"):
            version = line.split("=")[1].strip().replace("\"","")
