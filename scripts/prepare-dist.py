import os
import sys
import shutil
from pathlib import Path

def copy_mnfst(pkg_name):
    mnfst = 'MANIFEST.in'
    copied = f'MANIFEST.{pkg_name}.in'
    with open(mnfst, 'a') as f:
        with open(copied, 'r') as copied_f:
            lines = copied_f.readlines()
            for l in lines:
                f.write(l)

def rename_setup(pkg_name):
    fname = f'setup.{pkg_name}.py'
    if os.path.exists('setup.py'):
        os.rename('setup.py', 'setup.tmp.py')
    os.rename(fname, 'setup.py')

def prepare():
    try:
        pkg_name = sys.argv[1]
    except IndexError:
        pkg_name = 'orig'

    if pkg_name not in ('orig', 'client', 'client-cli'):
        print("The argument string must be one of ('', 'client', 'client-cli')")
        exit(1)

    copy_mnfst(pkg_name)
    rename_setup(pkg_name)

if __name__ == '__main__':
    prepare()
