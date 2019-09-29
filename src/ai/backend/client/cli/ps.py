import click

from . import main
from .admin.sessions import sessions


@main.command()
@click.option('-s', '--status', default=None,
              type=click.Choice([
                  'PENDING',
                  'PREPARING', 'BUILDING', 'RUNNING', 'RESTARTING',
                  'RESIZING', 'SUSPENDED', 'TERMINATING',
                  'TERMINATED', 'ERROR',
                  'ALL',  # special case
              ]),
              help='Filter by the given status')
@click.option('--id-only', is_flag=True, help='Display session ids only.')
@click.option('--show-tid', is_flag=True, help='Display task/kernel IDs.')
@click.option('--dead', is_flag=True,
              help='Filter only dead sessions. Ignores --status option.')
@click.option('--running', is_flag=True,
              help='Filter only scheduled and running sessions. Ignores --status option.')
@click.option('-a', '--all', is_flag=True,
              help='Display all sessions matching the condition using pagination.')
@click.option('--detail', is_flag=True, help='Show more details using more columns.')
@click.pass_context
def ps(ctx, status, id_only, show_tid, dead, running, all, detail):
    '''
    Lists the current running compute sessions for the current keypair.
    This is an alias of the "admin sessions --status=RUNNING" command.
    '''
    ctx.forward(sessions)
