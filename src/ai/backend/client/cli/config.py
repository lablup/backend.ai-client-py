import getpass
from pathlib import Path

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
    print('API endpoint: {0} ({1})'.format(
          click.style(str(config.endpoint), bold=True),
          click.style(str(config.endpoint_type), fg='cyan', bold=True)))
    print('API version: {0}'.format(click.style(config.version, bold=True)))
    if config.domain:
        print('Domain name: "{0}"'.format(click.style(config.domain, bold=True)))
    if config.group:
        print('Group name: "{0}"'.format(click.style(config.group, bold=True)))
    if config.is_anonymous:
        print('Access key: (this is an anonymous session)')
    elif config.endpoint_type == 'docker':
        pass
    else:
        print('Access key: "{0}"'.format(click.style(config.access_key, bold=True)))
        masked_skey = config.secret_key[:6] + ('*' * 24) + config.secret_key[-10:]
        print('Secret key: "{0}"'.format(click.style(masked_skey, bold=True)))
    print('Signature hash type: {0}'.format(
        click.style(config.hash_type, bold=True)))
    print('Skip SSL certificate validation? {0}'.format(
        click.style(str(config.skip_sslcert_validation), bold=True)))


@main.command()
def login():
    '''
    Log-in to the console API proxy.
    '''
    user_id = input('User ID: ')
    password = getpass.getpass()

    local_config_path = Path.home() / '.config' / 'backend.ai'
    local_config_path.mkdir(parents=True, exist_ok=True)
    with open(local_config_path / 'session.cfg', 'w') as f:
        ...
