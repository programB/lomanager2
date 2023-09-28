import argparse
import os
import pathlib
import shutil
import tarfile
import zipapp

import defs
import make_locales
import make_rpms

setup_dir = pathlib.Path("setup")
if not setup_dir.is_dir():
    print("This script must be called from the top level directory")
    exit(1)

src_dir = pathlib.Path("lomanager2")
locale_dir = pathlib.Path("i18n")

build_dir = pathlib.Path("build")
bin_dir = build_dir.joinpath("bin")
mo_dir = build_dir.joinpath("translations")

dist_dir = pathlib.Path("dist")
dist_SOURCES_dir = dist_dir.joinpath("SOURCES")
dist_SPECS_dir = dist_dir.joinpath("SPECS")
release_dir = dist_SOURCES_dir.joinpath(defs.__package__ + "-" + defs.__version__)

exe_filename = defs.__package__
exe_file = bin_dir.joinpath(exe_filename)

spec_filename = defs.__package__ + ".spec"
spec_file = build_dir.joinpath(spec_filename)


def make_dir(dir: pathlib.Path):
    if not dir.is_dir():
        print(f"Creating directory: {dir}")
        os.makedirs(dir, exist_ok=True)
    else:
        print(f"Using existing directory: {dir}")


def rm_dir(dir: pathlib.Path):
    if dir.is_dir():
        try:
            shutil.rmtree(dir)
        except Exception as error:
            print(f"Failed to remove: {dir}")
            print(error)
            exit(1)
        else:
            print(f"Removed: {dir}")


def create_executable():
    def excluded_files_and_dirs(item):
        excluded_dirs = ["__pycache__"]
        excluded_f_exts = [".pyc", ".pyo"]
        item = src_dir.joinpath(item)
        if (item.is_dir() and item.name in excluded_dirs) or (
            item.is_file() and item.suffix in excluded_f_exts
        ):
            print(f"Exluding {item.name}")
            return False
        return True

    try:
        # Create bin dir if it doesn't exist
        os.makedirs(bin_dir, exist_ok=True)
        zipapp.create_archive(
            source=src_dir,
            target=exe_file,
            interpreter="/usr/bin/env python3",
            main=None,
            filter=excluded_files_and_dirs,
            compressed=False,
        )
    except Exception as error:
        print(f"Failed to pack sources to archive {exe_file}")
        print(error)
        exit(1)
    else:
        print(f"Packed sources to archive {exe_file}")


def compile_translations():
    try:
        # Create compiled translations dir if it doesn't exist
        os.makedirs(mo_dir, exist_ok=True)
        make_locales.compile(target_dir=mo_dir)
    except Exception as error:
        print("Failed to compile translations files (.mo)")
        print(error)
        exit(1)


def create_spec():
    try:
        make_rpms.create_spec_file(target=spec_file)
    except Exception as error:
        print("Failed to create .spec file")
        print(error)
        exit(1)


def copy_exe_to(dir: pathlib.Path):
    target = dir.joinpath(exe_file.name)
    try:
        shutil.copyfile(exe_file, target)
    except Exception as error:
        print(f"Failed to copy {exe_file} to {target}")
        print(error)
        exit(1)
    else:
        print(f"Copied: {exe_file} to {target}")


def copy_mo_files_to(dir: pathlib.Path):
    print(f"Copying .mo files from {mo_dir} to {dir}")
    for mofile in mo_dir.glob("*.mo"):
        target = dir.joinpath(mofile.name)
        try:
            shutil.copyfile(mofile, target)
        except Exception as error:
            print(f"Failed to copy {mofile.name} to {target}")
            print(error)
            exit(1)
        else:
            print(f"Copied: {mofile.name} to {target}")


def pack_release(rel_dir: pathlib.Path, target_dir: pathlib.Path):
    archive_format = {"type": "xz", "ext": ".tar.xz"}
    archive_filename = rel_dir.name + archive_format["ext"]
    archive_file = target_dir.joinpath(archive_filename)
    try:
        tar = tarfile.open(archive_file, f"w:{archive_format['type']}")
        start_dir = os.getcwd()
        os.chdir(archive_file.parent)
        tar.add(rel_dir.name)
        tar.close
        os.chdir(start_dir)
    except Exception as error:
        print(f"Failed to pack {rel_dir} to a {archive_file}")
        print(error)
        exit(1)
    else:
        print(f"Packed: {rel_dir} as {archive_file}")


def copy_docs_to(dir: pathlib.Path):
    help_f = pathlib.Path("docs").joinpath("help.md")
    target = dir.joinpath(help_f.name)
    try:
        shutil.copyfile(help_f, target)
    except Exception as error:
        print(f"Failed to Copy: {help_f} to {target}")
        print(error)
        exit(1)
    else:
        print(f"Copied: {help_f} to {target}")


def copy_spec_to(dir: pathlib.Path):
    target = dir.joinpath(spec_file.name)
    try:
        shutil.copyfile(spec_file, target)
    except Exception as error:
        print(f"Failed to copy: {spec_file} to {target}")
        print(error)
        exit(1)
    else:
        print(f"Copied: {spec_file} to {target}")


def command_make_exe():
    make_dir(build_dir)
    create_executable()


def command_make_translations():
    make_dir(build_dir)
    compile_translations()


def command_make_spec():
    make_dir(build_dir)
    create_spec()


def command_build_all():
    command_make_exe()
    command_make_translations()
    command_make_spec()


def command_make_dist():
    make_dir(dist_SPECS_dir)
    copy_spec_to(dist_SPECS_dir)

    make_dir(dist_SOURCES_dir)
    copy_docs_to(dist_SOURCES_dir)

    make_dir(release_dir)
    copy_exe_to(release_dir)
    copy_mo_files_to(release_dir)
    pack_release(release_dir, dist_SOURCES_dir)
    rm_dir(release_dir)


def command_clean_build():
    rm_dir(build_dir)


def command_clean_dist():
    rm_dir(dist_dir)


def command_send_to_build_machine():
    remote_dir = pathlib.Path("~/tmp/VBOX_rpm_build_server/rpm_build/").expanduser()
    try:
        shutil.copytree(dist_dir, remote_dir, dirs_exist_ok=True)
    except Exception as error:
        print(f"Failed to copy {dist_dir} to {remote_dir}")
        print(error)
        exit(1)
    else:
        print(f"Copied {dist_dir} to {remote_dir}")


# def build_rpms(RPM=True, SRPM=True):
#     if RPM:
#         try:
#             print(f"Building binary .rpm package")
#             subprocess.run(["rpmbuild", "-bb", f"{defs.SPECS}/{spec_filename}"])
#         except Exception as error:
#             print(error)
#             exit(1)
#         else:
#             print("Success")
#     if SRPM:
#         try:
#             print(f"Building  src.rpm package")
#             subprocess.run(["rpmbuild", "-bs", f"{defs.SPECS}/{spec_filename}"])
#         except Exception as error:
#             print(error)
#             exit(1)
#         else:
#             print("Success")


def main():
    parser = argparse.ArgumentParser(description="lomanager2 build tooling")
    subcommands = parser.add_subparsers(title="subcommands")

    ######################
    build_all_p = subcommands.add_parser(
        "build_all",
        help=("build all assets"),
    )
    build_all_p.set_defaults(func=command_build_all)
    #
    dist_p = subcommands.add_parser(
        "dist",
        help=("create distribution"),
    )
    dist_p.set_defaults(func=command_make_dist)
    #
    exe_p = subcommands.add_parser(
        "exe",
        help=("build executable file from sources"),
    )
    exe_p.set_defaults(func=command_make_exe)
    #
    translations_p = subcommands.add_parser(
        "translations",
        help=("compile translations into .mo files"),
    )
    translations_p.set_defaults(func=command_make_translations)
    #
    spec_p = subcommands.add_parser(
        "spec",
        help=("create .spec file"),
    )
    spec_p.set_defaults(func=command_make_spec)
    #
    clean_build_p = subcommands.add_parser(
        "clean_build",
        help=("remove build dir"),
    )
    clean_build_p.set_defaults(func=command_clean_build)
    #
    clean_dist_p = subcommands.add_parser(
        "clean_dist",
        help=("remove dist dir"),
    )
    clean_dist_p.set_defaults(func=command_clean_dist)
    #
    send_to_build_machine = subcommands.add_parser(
        "send_for_packing",
        help=("Send files to remote machine that builds RPMs and SRPMs"),
    )
    send_to_build_machine.set_defaults(func=command_send_to_build_machine)
    ######################

    args = parser.parse_args()
    # Call
    args.func()


if __name__ == "__main__":
    main()
