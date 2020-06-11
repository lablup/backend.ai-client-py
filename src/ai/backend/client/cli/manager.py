import sys
import time

import click
from tabulate import tabulate

from . import main
from .pretty import print_wait, print_done
from ..session import Session


@main.group()
def manager():
    '''Provides manager-related operations.'''
    print('Run with -h/--help for usage.')


@manager.command()
def status():
    '''Show the manager's current status.'''
    with Session() as session:
        resp = session.Manager.status()
        print(tabulate([('Status', 'Active Sessions'),
                        (resp['status'], resp['active_sessions'])],
                       headers='firstrow'))


@manager.command()
@click.option('--wait', is_flag=True,
              help='Hold up freezing the manager until '
                   'there are no running sessions in the manager.')
@click.option('--force-kill', is_flag=True,
              help='Kill all running sessions immediately and freeze the manager.')
def freeze(wait, force_kill):
    '''Freeze manager.'''
    if wait and force_kill:
        print('You cannot use both --wait and --force-kill options '
              'at the same time.', file=sys.stderr)
        return

    with Session() as session:
        if wait:
            while True:
                resp = session.Manager.status()
                active_sessions_num = resp['active_sessions']
                if active_sessions_num == 0:
                    break
                print_wait('Waiting for all sessions terminated... ({0} left)'
                           .format(active_sessions_num))
                time.sleep(3)
            print_done('All sessions are terminated.')

        if force_kill:
            print_wait('Killing all sessions...')

        session.Manager.freeze(force_kill=force_kill)

        if force_kill:
            print_done('All sessions are killed.')

        print('Manager is successfully frozen.')


@manager.command()
def unfreeze():
    '''Unfreeze manager.'''
    with Session() as session:
        session.Manager.unfreeze()
        print('Manager is successfully unfrozen.')


@main.group()
def announcement():
    '''Global announcement related commands'''


@announcement.command()
def get():
    '''Get current announcement.'''
    with Session() as session:
        result = session.Manager.get_announcement()
        if result.get('enabled', False):
            msg = result.get('message')
            print(msg)
        else:
            print('No announcements.')


@announcement.command()
@click.argument('message', type=click.STRING)
def update(message):
    '''
    Post new announcement.

    MESSAGE: Announcement message.
    '''
    with Session() as session:
        session.Manager.update_announcement(enabled=True, message=message)
        print('Posted new announcement.')


@announcement.command()
def delete():
    '''Delete current announcement.'''
    confirm = input('Are you sure? (y/n) ')
    if confirm.lower() != 'y':
        print('canceled.')
        sys.exit(1)
    with Session() as session:
        session.Manager.update_announcement(enabled=False)
    print('Deleted announcement.')
