from setuptools import setup, find_namespace_packages
from typing import List
from pathlib import Path
import re

setup_requires = [
    'setuptools>=54.2.0',
]
install_requires = [
    'aiohttp~=3.7.4',
    'aiotusclient~=0.1.4',
    'appdirs~=1.4.4',
    'async_timeout>=3.0',
    'attrs>=21.2',
    'click>=8.0.1',
    'colorama>=0.4.4',
    'humanize>=3.1.0',
    'janus>=0.6.1',
    'multidict>=5.1.0',
    'python-dateutil>=2.8.2',
    'PyYAML~=5.4.1',
    'tabulate>=0.8.9',
    'tqdm>=4.61',
    'typing-extensions>=3.10.0',
    'yarl>=1.6.3',
    'backend.ai-cli~=0.5.0.post1',
]
build_requires = [
    'wheel>=0.36.2',
    'twine>=3.4.2',
    'towncrier>=21.3.0',
]
test_requires = [
    'pytest~=6.2.4',
    'pytest-cov',
    'pytest-mock',
    'pytest-asyncio>=0.15.1',
    'aioresponses>=0.7.2',
    'asynctest>=0.13; python_version<"3.8"',
    'codecov',
]
lint_requires = [
    'flake8>=3.9.2',
]
typecheck_requires = [
    'mypy>=0.910',
    'types-click',
    'types-python-dateutil',
    'types-tabulate',
]
dev_requires: List[str] = [
    # 'pytest-sugar>=0.9.1',
]
docs_requires = [
    'Sphinx~=3.4.3',
    'sphinx-intl>=2.0',
    'sphinx_rtd_theme>=0.4.3',
    'sphinxcontrib-trio>=1.1.0',
    'sphinx-autodoc-typehints~=1.11.1',
    'pygments~=2.7.4',
]


def read_src_version():
    path = (Path(__file__).parent / 'src' /
            'ai' / 'backend' / 'client' / '__init__.py')
    src = path.read_text(encoding='utf-8')
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
    long_description=Path('README.rst').read_text(encoding='utf-8'),
    url='https://github.com/lablup/backend.ai-client-py',
    author='Lablup Inc.',
    author_email='joongi@lablup.com',
    license='MIT',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Operating System :: POSIX',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Environment :: No Input/Output (Daemon)',
        'Topic :: Scientific/Engineering',
        'Topic :: Software Development',
    ],
    package_dir={'': 'src'},
    packages=find_namespace_packages(where='src', include='ai.backend.*'),
    python_requires='>=3.7',
    setup_requires=setup_requires,
    install_requires=install_requires,
    extras_require={
        'dev': dev_requires,
        'build': build_requires,
        'test': test_requires,
        'lint': lint_requires,
        'typecheck': typecheck_requires,
        'docs': docs_requires,
    },
    data_files=[],
    package_data={
        'ai.backend.client': ['py.typed'],
    },
    entry_points={
        'backendai_cli_v10': [
            '_ = ai.backend.client.cli:main',
        ]
    },
)
