from pathlib import Path
from setuptools import setup, find_namespace_packages

from setup_orig import setup_args, install_requires as base_requires, read_src_version

install_requires = {
    'click': base_requires['click'],
    'colorama': base_requires['colorama'],
    'humanize': base_requires['humanize'],
    'rich': base_requires['rich'],
    'tabulate': base_requires['tabulate'],
    'tqdm': base_requires['tqdm'],
    'backend.ai-client-sdk': '>=22.03.0a2',
}

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
                version = read_src_version(
                    path = (Path(__file__).parent / 'src' / 'ai' /
                    'backend' / 'client' / 'cli' / '__init__.py'),
                ),
                install_requires = \
                    [f'{r}{ver}' for r, ver in install_requires.items()],
            ),
    ))
