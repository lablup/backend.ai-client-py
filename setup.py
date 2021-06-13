from setuptools import setup, find_namespace_packages
from typing import List
from pathlib import Path
import re

setup_requires = [
    'setuptools>=54.2.0',
]
install_requires = [
    'backend.ai-cli~=0.4.1',
    'aiohttp~=3.7.4',
    'aiotusclient~=0.1.3',
    'appdirs~=1.4.3',
    'async_timeout~=3.0',  # to avoid pip10 resolver issue
    'attrs>=20.1',         # to avoid pip10 resolver issue
    'click~=7.1.2',
    'colorama~=0.4.3',
    'humanize~=3.1.0',
    'janus~=0.6.0',
    'multidict~=4.7.4',
    'python-dateutil~=2.8.1',
    'PyYAML~=5.4.1',
    'tabulate~=0.8.6',
    'tqdm~=4.48',
    'yarl~=1.6.1',
    'typing-extensions~=3.7.4',
]
build_requires = [
    'wheel>=0.36.2',
    'twine>=3.4.1',
    'towncrier>=21.3.0',
]
test_requires = [
    'pytest~=6.1.1',
    'pytest-cov',
    'pytest-mock',
    'pytest-asyncio>=0.12.0',
    'aioresponses~=0.7.0',
    'asynctest>=0.13; python_version<"3.8"',
    'codecov',
]
lint_requires = [
    'flake8>=3.8.4',
]
typecheck_requires = [
    'mypy>=0.901',
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
    entry_points={
        'backendai_cli_v10': [
            '_ = ai.backend.client.cli:main',
        ]
    },
)
