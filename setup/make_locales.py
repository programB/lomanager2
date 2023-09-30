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
import os
import pathlib
import shutil
import subprocess

import defs

supported_langs = [
    "bg_BG",
    "ca_ES",
    "cs_CZ",
    "de_DE",
    "el_GR",
    "es_ES",
    "fr_FR",
    "it_IT",
    "nl_NL",
    "pl_PL",
    "pt_PT",
    "ru_RU",
    "sr",
    "uk_UA",
]

setup_dir = pathlib.Path("setup")
if not setup_dir.is_dir():
    print("This script must be called from the top level directory")
    exit(1)

src_dir = pathlib.Path("lomanager2")
locale_dir = pathlib.Path("i18n")
domain = defs.__package__
main_pot_file = locale_dir.joinpath(domain + ".pot")


def run_shell_command(cmd: str, shell="bash", timeout=20, err_check=True):
    if cmd:
        full_command = [shell] + ["-c"] + [cmd]
        # print(f"Attempting to execute command: {full_command}")

        try:
            shellcommand = subprocess.run(
                full_command,
                check=err_check,  # some commands return non-zero exit code if successful
                timeout=timeout,  # fail on command taking to long to exec.
                capture_output=True,  # capture both stdout and stderr
                text=True,  # give the output as a string not bytes
                encoding="utf-8",
            )
            answer = (shellcommand.stdout + shellcommand.stderr).strip()
            # print(f"Received answer: {answer}")
        except FileNotFoundError as exc:
            print(f"Executable not be found. {str(exc)}")
        except subprocess.CalledProcessError as exc:
            print(f"Error: {str(exc)}")
        except subprocess.TimeoutExpired as exc:
            print(exc)
    else:
        print("An empty string passed as a command to be executed!")


def print_locale_dir():
    print(locale_dir)


def print_langs():
    for lang_code in supported_langs:
        print(lang_code)


def create_main_po_template():
    if not main_pot_file.exists():
        print(f"Creating new translation template ({main_pot_file})")
        os.makedirs(main_pot_file.parent, exist_ok=True)
        main_pot_file.touch()
    else:
        print(f"Found existing translation template ({main_pot_file})")

    for pythonfile in src_dir.glob("**/*.py"):
        print(f"Extracting strings from:   {pythonfile}")
        run_shell_command(
            rf"xgettext --join-existing -L Python -o {main_pot_file} {pythonfile}"
        )


def init_langs():
    print("Creating .po files for supported languages")
    for lang_code in supported_langs:
        # For language codes in the list use the .pot template to generate .po
        # files
        # --locale
        # is for msginit to decide what filename of the .po
        # file should be based on the langcode passed in
        # eg. el_GR will produce el.po
        # This option also ensures that the charset used to create the file is UTF-8.
        # --no-translator
        # removes the need to fill in translator name and email
        run_shell_command(
            rf"msginit --no-translator --input={main_pot_file} --locale={lang_code}.UTF-8"
        )
        print(f"file created for: {lang_code}")
    # Move created po files to translation directory
    # changing their names to lomanager2_<msginit assigned lang code>.po
    # eg. lomanager2_el.po
    print(f"Renaming .po files and moving them to locale directory: {locale_dir}")
    for pofile in pathlib.Path(".").glob("*.po"):
        gettext_lang_code = pofile.stem
        po_filename = domain + "_" + gettext_lang_code + ".po"
        try:
            dst = locale_dir.joinpath(po_filename)
            shutil.move(src=pofile, dst=dst)
            print(f"Created: {dst}")
        except Exception as error:
            print(f"Error when moving {pofile} to {locale_dir}: {str(error)}")


def merge():
    print("Merging existing translations with the new template")
    po_files = list(locale_dir.glob("**/*.po"))
    if po_files:
        for pofile in po_files:
            print(f"Modifying: {pofile}")
            run_shell_command(
                rf"msgmerge --multi-domain --previous --update {pofile} {main_pot_file}"
            )
    else:
        print("Error: No translation files (.po) found.")


def compile(target_dir: pathlib.Path):
    print("Compiling translations in .po files into .mo files")
    for pofile in locale_dir.glob("**/*.po"):
        # mofile = pofile.parent.joinpath(pofile.stem + ".mo")
        mofile = target_dir.joinpath(pofile.stem + ".mo")
        print(f"Creating: {mofile}")
        run_shell_command(rf"msgfmt {pofile} -o {mofile}")


def clean():
    # Do not delete locale directory itself nor the template file .pot
    if locale_dir.is_dir():
        print(f"Cleaning locale directory {locale_dir}")
        for item in locale_dir.iterdir():
            if item.is_dir():
                try:
                    shutil.rmtree(item)
                except Exception as error:
                    print(error)
            elif item.is_file() and item != main_pot_file:
                try:
                    os.remove(item)
                except Exception as error:
                    print(f"Error when removing {item}: {error}")
            else:
                print(f"{item} was not removed")
    else:
        print(f"locale directory ({locale_dir}) does not exist")


def purge():
    print(f"Attempting to completely remove locales directory ({locale_dir})")
    try:
        shutil.rmtree(locale_dir)
    except Exception as error:
        print(error)
    else:
        print("Success")


def workflow_initialize_translations():
    # Create .pot template, and .po files for all languages together
    # with relevant directory structure
    create_main_po_template()
    init_langs()


def workflow_update_translations():
    # Create new .pot template (replacing the old one)
    # Merge it with existing translations (.po files) for all languages
    create_main_po_template()
    merge()


def workflow_compile_translations():
    compile(locale_dir)


def main():
    parser = argparse.ArgumentParser(description="Localize lomanager2")
    subcommands = parser.add_subparsers(title="subcommands")

    dir_p = subcommands.add_parser(
        "dir",
        help=("Prints the locale folder that was set for this script"),
    )
    dir_p.set_defaults(func=print_locale_dir)

    langs_p = subcommands.add_parser(
        "langs",
        help=("Prints all language codes for which translation file will be generated"),
    )
    langs_p.set_defaults(func=print_langs)

    init_p = subcommands.add_parser(
        "init",
        help=(
            "Extract translatable strings from .py files and create template"
            " file (.pot), then create translation files (.po) for all languages"
        ),
    )
    init_p.set_defaults(func=workflow_initialize_translations)

    update_p = subcommands.add_parser(
        "update",
        help=(
            "Create new translation template file (.pot) replacing "
            "the old one and merge it with existing translations (.po files)"
        ),
    )
    update_p.set_defaults(func=workflow_update_translations)

    compile_p = subcommands.add_parser(
        "compile", help="Compile translations in .po files into .mo files"
    )
    compile_p.set_defaults(func=workflow_compile_translations)

    clean_p = subcommands.add_parser(
        "clean",
        help=(
            "Remove all translation files (.po, .mo) and subdirectories. "
            "Do not remove locale directory itself nor the template (.pot) file"
        ),
    )
    clean_p.set_defaults(func=clean)

    purge_p = subcommands.add_parser(
        "purge", help="Completely remove locales directory"
    )
    purge_p.set_defaults(func=purge)
    args = parser.parse_args()

    # Call
    args.func()


if __name__ == "__main__":
    main()
