import warnings

import click

from .. import __version__
from ..config import APIConfig, set_config
from ai.backend.cli.extensions import ExtendedCommandGroup


@click.group(
    cls=ExtendedCommandGroup,
    context_settings={
        'help_option_names': ['-h', '--help'],
    },
)
@click.option('--skip-sslcert-validation',
              help='Skip SSL certificate validation for all API requests.',
              is_flag=True)
@click.version_option(version=__version__)
def main(skip_sslcert_validation):
    """
    Backend.AI command line interface.
    """
    from .announcement import announce
    config = APIConfig(
        skip_sslcert_validation=skip_sslcert_validation,
        announcement_handler=announce,
    )
    set_config(config)

    from .pretty import show_warning
    warnings.showwarning = show_warning
