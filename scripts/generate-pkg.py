import os
import sys
import shutil
from pathlib import Path

def set_mnfst(pkg_name):
    mnfst = 'MANIFEST.orig.in'
    copied = f'MANIFEST.{pkg_name}.in'

    def append_mnfst():
        with open(mnfst, 'a') as f:
            with open(copied, 'r') as copied_f:
                lines = copied_f.readlines()
                for l in lines:
                    f.write(l)

    def copy_to_tmp_workspace():
        os.makedirs(f'./tmp/{pkg_name}', exist_ok=True)
        with open (mnfst, 'r') as f:
            lines = f.readlines()
            for l in lines:
                cmd, _, src = l.rstrip('\n').partition(' ')
                subtree_path = Path(src).parts
                if src.startswith('src'):
                    subtree_path = ['src', *subtree_path[1:]]
                dst = Path('tmp', pkg_name, *subtree_path)
                if cmd == 'include':
                    shutil.copyfile(src, dst)
                elif cmd == 'graft':
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                elif cmd in ('exclude', 'prune'):
                    shutil.rmtree(dst)

    def copy_mnfst():
        dst = Path('tmp', pkg_name, 'MANIFEST.in')
        shutil.copyfile(mnfst, dst)

    append_mnfst()
    copy_to_tmp_workspace()
    copy_mnfst()

def copy_setup(pkg_name):
    setup_name = f'setup.{pkg_name}.py'
    dst = Path('tmp', pkg_name, 'setup.py')
    shutil.copyfile(setup_name, dst)

def generate():
    try:
        pkg_name = sys.argv[1]
    except IndexError:
        pkg_name = None

    if pkg_name not in ('client', 'client-cli'):
        print("The argument string must be one of ('client', 'client-cli')")
        exit(1)

    set_mnfst(pkg_name)
    copy_setup(pkg_name)

if __name__ == '__main__':
    generate()
