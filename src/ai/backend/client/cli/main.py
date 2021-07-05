import warnings

import click

from .. import __version__
from ..config import APIConfig, set_config
from .types import CLIContext, OutputMode

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
@click.option('--output', type=click.Choice(['json', 'console']), default='console',
              help='Set the output style of the command results.')
@click.version_option(version=__version__)
@click.pass_context
def main(ctx: click.Context, skip_sslcert_validation: bool, output: str) -> None:
    """
    Backend.AI command line interface.
    """
    from .announcement import announce
    config = APIConfig(
        skip_sslcert_validation=skip_sslcert_validation,
        announcement_handler=announce,
    )
    set_config(config)

    cli_ctx = CLIContext(
        api_config=config,
        output_mode=OutputMode(output),
    )
    ctx.obj = cli_ctx

    from .pretty import show_warning
    warnings.showwarning = show_warning
