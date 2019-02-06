import click

from . import main
from .. import __version__
from ..config import get_config


@main.command()
def config():
    '''
    Shows the current configuration.
    '''
    config = get_config()
    print('Client version: {0}'.format(click.style(__version__, bold=True)))
    print('API endpoint: {0}'.format(click.style(str(config.endpoint), bold=True)))
    print('API version: {0}'.format(click.style(config.version, bold=True)))
    print('Access key: "{0}"'.format(click.style(config.access_key, bold=True)))
    masked_skey = config.secret_key[:6] + ('*' * 24) + config.secret_key[-10:]
    print('Secret key: "{0}"'.format(click.style(masked_skey, bold=True)))
    print('Signature hash type: {0}'.format(
        click.style(config.hash_type, bold=True)))
    print('Skip SSL certificate validation? {0}'.format(
        click.style(str(config.skip_sslcert_validation), bold=True)))
