import time

from tabulate import tabulate

from . import register_command
from .pretty import print_wait, print_done
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
        if args.wait:
            while True:
                resp = session.Manager.status()
                active_sessions_num = resp['active_sessions']
                if active_sessions_num == 0:
                    break
                print_wait('Waiting for all sessions terminated... ({0} left)'
                           .format(active_sessions_num))
                time.sleep(3)
            print_done('All sessions are terminated.')
        session.Manager.freeze()
        print('Manager is successfully frozen.')


freeze.add_argument('--wait', action='store_true', default=False,
                    help='Hold up freezing the manager until '
                         'there are no running sessions in the manager.')


@manager.register_command
def unfreeze(args):
    '''Unfreeze manager.'''
    with Session() as session:
        session.Manager.unfreeze()
        print('Manager is successfully unfrozen.')
