import os
import sys
import shutil
from pathlib import Path

def copy_from_mnfst(pkg_name):
    mnfst = 'MANIFEST.in'
    copied = f'MANIFEST.{pkg_name}.in'
    with open(mnfst, 'a') as f:
        with open(copied, 'r') as copied_f:
            lines = copied_f.readlines()
            for l in lines:
                f.write(l)

    os.mkdir('./tmp')
    with open (mnfst, 'r') as f:
        lines = f.readlines()
        for l in lines:
            cmd, _, src = l.rstrip('\n').partition(' ')
            subtree_path = Path(src).parts
            if src.startswith('src'):
                subtree_path = subtree_path[1:]
            if cmd == 'include':
                shutil.copyfile(src, Path('tmp', *subtree_path))
            elif cmd == 'graft':
                shutil.copytree(src, Path('tmp', *subtree_path), dirs_exist_ok=True)
            elif cmd in ('exclude', 'prune'):
                shutil.rmtree(Path('tmp', *subtree_path))

def rename_setup(pkg_name):
    fname = f'setup.{pkg_name}.py'
    if os.path.exists('setup.py'):
        os.rename('setup.py', '_setup.py')
    os.rename(fname, 'setup.py')

def generate():
    try:
        pkg_name = sys.argv[1]
    except IndexError:
        pkg_name = 'orig'

    if pkg_name not in ('orig', 'client', 'client-cli'):
        print("The argument string must be one of ('', 'client', 'client-cli')")
        exit(1)

    copy_from_mnfst(pkg_name)
    rename_setup(pkg_name)

if __name__ == '__main__':
    generate()
