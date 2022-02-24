import os
import sys
import shutil
from pathlib import Path

def copy_mnfst(pkg_name):
    fname = f'MANIFEST.{pkg_name}.in'
    with open(fname, 'r') as f:
        lines = f.readlines()
        for l in lines:
            cmd, _, src = l.rstrip('\n').partition(' ')
            if src.startswith('src'):
                if cmd == 'include':
                    dpath = Path(src).parts
                    shutil.copy(src, Path(f'src-{pkg_name}', *dpath[1:]))
                elif cmd == 'graft':
                    dpath = Path(src).parts
                    shutil.copytree(src, Path(f'src-{pkg_name}', *dpath[1:]))
    os.rename('src', 'src-orig')
    os.rename(f'src-{pkg_name}', 'src')
    
    os.rename('MANIFEST.in', 'MANIFEST.tmp.in')
    os.rename(fname, 'MANIFEST.in')

def copy_setup(pkg_name):
    fname = f'setup.{pkg_name}.py'
    os.rename('setup.py', 'setup.tmp.py')
    os.rename(fname, 'setup.py')

def generate():
    try:
        pkg_name = sys.argv[1]
    except IndexError:
        pkg_name = ''

    if pkg_name not in ('', 'client', 'cli', 'dev'):
        print("The argument string must be one of ('', 'client', 'cli', 'dev')")
        exit(1)

    if pkg_name != '':
        copy_mnfst(pkg_name)
        copy_setup(pkg_name)

if __name__ == '__main__':
    generate()
