from . import register_command
from ..session import Session


@register_command
def manager(args):
    '''Provides manager-related operations.'''
    print('Run with -h/--help for usage.')


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
