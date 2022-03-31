from setuptools import setup
from setup_orig import setup_args, install_requires

pruned_req = {
    'aiohttp',
    'aiotusclient',
    'appdirs',
    'async_timeout',
    'attrs',
    'janus',
    'multidict',
    'python-dateutil',
    'PyYAML',
    'yarl',
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
                install_requires = \
                    [f'{r}{ver}' for r, ver in install_requires.items() if r not in pruned_req]
            ),
    ))
