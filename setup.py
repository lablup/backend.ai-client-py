from setuptools import setup, find_namespace_packages
from pathlib import Path
import re

setup_requires = [
    'setuptools>=40.2.0',
]
install_requires = [
    'multidict>=4.0',
    'aiohttp~=3.4.0',
    'async_timeout~=3.0',  # to avoid pip10 resolver issue
    'attrs>=18.0',       # to avoid pip10 resolver issue
    'namedlist>=1.6',
    'python-dateutil>=2.5',
    'ConfigArgParse==0.12.0',
    'tabulate>=0.7.7',
    'tqdm~=4.21',
    'humanize>=0.5.1',
    'yarl>=1.1.1',
]
build_requires = [
    'wheel>=0.31.0',
    'twine>=1.11.0',
]
test_requires = [
    'pytest~=3.9.0',
    'pytest-cov',
    'pytest-mock',
    'pytest-asyncio>=0.9.0',
    'aioresponses>=0.4.2',
    'asynctest>=0.12.2',
    'codecov',
    'flake8>=3.6',
]
ci_requires = [
] + build_requires + test_requires
dev_requires = [
    'pytest-sugar>=0.9.1',
] + build_requires + test_requires


def read_src_version():
    path = (Path(__file__).parent / 'src' /
            'ai' / 'backend' / 'client' / '__init__.py')
    src = path.read_text()
    m = re.search(r"^__version__ = '([^']+)'$", src, re.MULTILINE)
    assert m is not None, 'Could not read the version information!'
    return m.group(1)


setup(
    name='backend.ai-client',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version=read_src_version(),
    description='Backend.AI Client for Python',
    long_description=Path('README.rst').read_text(),
    url='https://github.com/lablup/backend.ai-client-py',
    author='Lablup Inc.',
    author_email='joongi@lablup.com',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)',  # noqa
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Operating System :: POSIX',
        'Operating System :: MacOS :: MacOS X',
        'Environment :: No Input/Output (Daemon)',
        'Topic :: Scientific/Engineering',
        'Topic :: Software Development',
    ],
    package_dir={'': 'src'},
    packages=find_namespace_packages(where='src', include='ai.backend.*'),
    python_requires='>=3.5',
    setup_requires=setup_requires,
    install_requires=install_requires,
    extras_require={
        'dev': dev_requires,
        'test': test_requires,
        'ci': ci_requires,
    },
    data_files=[],
    entry_points={
        'console_scripts': [
            'backend.ai = ai.backend.client.cli:main',
            'lcc = ai.backend.client.cli:main',
            'lpython = ai.backend.client.cli:main',
        ],
    },
)
