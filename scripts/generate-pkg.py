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
    appended = f'MANIFEST.{pkg_name}.in'

    copied_mnfst = Path('tmp', pkg_name, mnfst)
    copied_appended = Path('tmp', pkg_name, appended)

    def copy_mnfst():
        shutil.copyfile(mnfst, copied_mnfst)
        shutil.copyfile(appended, copied_appended)

    def append_manifest():
        with (
            open(copied_mnfst, 'a') as dst_file,
            open(copied_appended, 'r') as pkg_specific_file,
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

    copy_mnfst()
    if pkg_name != 'orig':
        append_manifest()
    copy_to_tmp_workspace()
    os.rename(copied_mnfst, Path('tmp', pkg_name, 'MANIFEST.in'))


def copy_setup(pkg_name):
    setup_name = f'setup_{pkg_name}.py'
    dst = Path('tmp', pkg_name, 'setup.py')
    shutil.copyfile(setup_name, dst)


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


if __name__ == '__main__':
    generate()
