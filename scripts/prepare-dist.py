import argparse
import os


def copy_manifest(pkg_name):
    dst = 'MANIFEST.in'
    src = f'MANIFEST.{pkg_name}.in'
    with (
        open(dst, 'a') as dst_file,
        open(src, 'r') as src_file,
    ):
        for line in src_file:
            dst_file.write(line)


def rename_setup(pkg_name):
    fname = f'setup.{pkg_name}.py'
    if os.path.exists('setup.py'):
        os.rename('setup.py', 'setup.tmp.py')
    os.rename(fname, 'setup.py')


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        'pkg_name',
        choices=['orig', 'client', 'client-cli'],
        default='orig',
        help="The target package to build",
    )
    args = argparser.parse_args()
    copy_manifest(args.pkg_name)
    rename_setup(args.pkg_name)


if __name__ == '__main__':
    main()
