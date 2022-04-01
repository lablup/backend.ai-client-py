import argparse
import os
import shutil
from pathlib import Path


def set_manifest(pkg_name):
    """
    Append the package-specific manifest to the integrated manifest.
    Package-specific manifests have files/directories to exclude from their final packages.
    Copy or remove files and directories to tmp/<package_name>/ as manifest.
    This step let type checker or linter check any dangling import.
    """
    mnfst = 'MANIFEST.orig.in'
    copied = f'MANIFEST.{pkg_name}.in'

    def append_manifest():
        with (
            open(mnfst, 'a') as dst_file,
            open(copied, 'r') as pkg_specific_file,
        ):
            for line in pkg_specific_file:
                dst_file.write(line)

    def copy_to_tmp_workspace():
        workspace_dir = Path('tmp', pkg_name)
        os.makedirs(workspace_dir, exist_ok=True)
        with open(mnfst, 'r') as manifest_file:
            for line in manifest_file:
                cmd, _, src = line.rstrip('\n').partition(' ')
                subtree_path = Path(src).parts
                dst = Path('tmp', pkg_name, *subtree_path)
                if cmd == 'include':
                    shutil.copyfile(src, dst)
                elif cmd == 'graft':
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                elif cmd == 'exclude':
                    os.unlink(dst)
                elif cmd == 'prune':
                    shutil.rmtree(dst)

    def copy_mnfst():
        dst = Path('tmp', pkg_name, 'MANIFEST.in')
        shutil.copyfile(mnfst, dst)

    append_manifest()
    copy_to_tmp_workspace()
    copy_mnfst()


def copy_setup(pkg_name):
    setup_name = f'setup_{pkg_name}.py'
    dst = Path('tmp', pkg_name, 'setup.py')
    shutil.copyfile(setup_name, dst)


def remove_duplicate_files():
    """
    Since type-checker raise 'Duplicate module name' error,
    unused duplicated named files should be unlinked
    """

    for dup_file_name in ('setup.py', 'setup_orig.py'):
        if os.path.exists(dup_file_name):
            os.unlink(dup_file_name)


def generate():
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        'pkg_names',
        nargs='*',
        choices=['orig', 'client', 'client-cli'],
        default='orig',
        help="The target package to build",
    )
    args = argparser.parse_args()
    for pkg_name in args.pkg_names:
        set_manifest(pkg_name)
        copy_setup(pkg_name)
    remove_duplicate_files()


if __name__ == '__main__':
    generate()
