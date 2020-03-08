from pathlib import Path
import sys
import warnings

import click

from ..config import APIConfig, set_config
from ai.backend.cli.extensions import AliasGroup


@click.group(cls=AliasGroup,
             context_settings={'help_option_names': ['-h', '--help']})
@click.option('--skip-sslcert-validation',
              help='Skip SSL certificate validation for all API requests.',
              is_flag=True)
@click.version_option()
def main(skip_sslcert_validation):
    """
    Backend.AI command line interface.
    """
    config = APIConfig(skip_sslcert_validation=skip_sslcert_validation)
    set_config(config)

    from .pretty import show_warning
    warnings.showwarning = show_warning


@click.command(context_settings=dict(ignore_unknown_options=True,
                                     allow_extra_args=True))
def run_alias():
    """
    Quick aliases for run command.
    """
    mode = Path(sys.argv[0]).stem
    help = True if len(sys.argv) <= 1 else False
    if mode == 'lcc':
        sys.argv.insert(1, 'c')
    elif mode == 'lpython':
        sys.argv.insert(1, 'python')
    sys.argv.insert(1, 'run')
    if help:
        sys.argv.append('--help')
    main.main(prog_name='backend.ai')


def _attach_command():
    from . import admin, config, app, files, logs, manager, proxy, ps, run  # noqa
    from . import vfolder       # noqa
    from . import session_template  # noqa
    from . import dotfile  # noqa


_attach_command()
