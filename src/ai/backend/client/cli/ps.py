import click

from . import main
from .admin.sessions import sessions


@main.command()
@click.option('-s', '--status', default=None,
              type=click.Choice([
                  'PENDING', 'SCHEDULED',
                  'PREPARING', 'BUILDING', 'RUNNING', 'RESTARTING',
                  'RESIZING', 'SUSPENDED', 'TERMINATING',
                  'TERMINATED', 'ERROR', 'CANCELLED',
                  'ALL',  # special case
              ]),
              help='Filter by the given status')
@click.option('--name-only', is_flag=True, help='Display session names only.')
@click.option('--dead', is_flag=True,
              help='Filter only dead sessions. Ignores --status option.')
@click.option('--running', is_flag=True,
              help='Filter only scheduled and running sessions. Ignores --status option.')
@click.option('--detail', is_flag=True, help='Show more details using more columns.')
@click.option('-f', '--format', default=None,  help='Display only specified fields.')
@click.option('--filter', 'filter_', default=None, help='Set the query filter expression.')
@click.option('--order', default=None, help='Set the query ordering expression.')
@click.option('--plain', is_flag=True,
              help='Display the session list without decorative line drawings and the header.')
@click.pass_context
def ps(ctx, status, name_only, dead, running, detail, filter_, order, plain, format):
    '''
    Lists the current running compute sessions for the current keypair.
    This is an alias of the "admin sessions --status=RUNNING" command.
    '''
    ctx.forward(sessions)
