from setuptools import setup
from pathlib import Path
import re

from setup_orig import setup_args, install_requires as base_requires

install_requires = {
    'click': base_requires['click'],
    'colorama': base_requires['colorama'],
    'humanize': base_requires['humanize'],
    'rich': base_requires['rich'],
    'tabulate': base_requires['tabulate'],
    'tqdm': base_requires['tqdm'],
    'backend.ai-client-sdk': '>=22.03.0a2',
}

def read_src_version():
    path = (Path(__file__).parent / 'src' /
            'ai' / 'backend' / 'client' / 'cli' / '__init__.py')
    src = path.read_text(encoding='utf-8')
    m = re.search(r"^__version__ = '([^']+)'$", src, re.MULTILINE)
    assert m is not None, 'Could not read the version information!'
    return m.group(1)

def get_filtered_args(setup_args, reqs_map):
    filtered_setup_args = {**setup_args}
    for req, req_list in reqs_map.items():
        filtered_setup_args[req] = req_list
    return filtered_setup_args

if __name__ == '__main__':
    setup(
        **get_filtered_args(
            setup_args,
            dict(
                name = 'backend.ai-client-cli',
                version = read_src_version(),
                install_requires = \
                    [f'{r}{ver}' for r, ver in install_requires.items()],
            ),
    ))
