import sys
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
    if args.wait and args.force_kill:
        print('You cannot use both --wait and --force-kill options '
              'at the same time.', file=sys.stderr)
        return

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

        if args.force_kill:
            print_wait('Killing all sessions...')

        session.Manager.freeze(force_kill=args.force_kill)

        if args.force_kill:
            print_done('All sessions are killed.')

        print('Manager is successfully frozen.')


freeze.add_argument('--wait', action='store_true', default=False,
                    help='Hold up freezing the manager until '
                         'there are no running sessions in the manager.')

freeze.add_argument('--force-kill', action='store_true', default=False,
                    help='Kill all running sessions immediately '
                         'and freeze the manager.')


@manager.register_command
def unfreeze(args):
    '''Unfreeze manager.'''
    with Session() as session:
        session.Manager.unfreeze()
        print('Manager is successfully unfrozen.')
