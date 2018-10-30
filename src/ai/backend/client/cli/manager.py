from tabulate import tabulate

from . import register_command
from ..session import Session


@register_command
def manager(args):
    '''Provides manager-related operations.'''
    print('Run with -h/--help for usage.')


@manager.register_command
def status(args):
    '''Show the manager's current status.'''
    with Session() as session:
        resp = session.Manager.status()
        print(tabulate([('Status', 'Active Sessions'),
                        (resp['status'], resp['active_sessions'])],
                       headers='firstrow'))


@manager.register_command
def freeze(args):
    '''Freeze manager.'''
    with Session() as session:
        session.Manager.freeze()
        print('Manager is successfully frozen.')


@manager.register_command
def unfreeze(args):
    '''Unfreeze manager.'''
    with Session() as session:
        session.Manager.unfreeze()
        print('Manager is successfully unfrozen.')
