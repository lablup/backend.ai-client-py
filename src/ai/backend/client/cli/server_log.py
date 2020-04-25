from datetime import datetime
import sys

import click

from . import main
from .pretty import print_wait, print_done, print_error, print_fail
from ..session import Session


@main.group()
def server_logs():
    '''Provides operations related to server logs.'''


@server_logs.command()
@click.option('--mark-read', is_flag=True, default=False,
              help='Mark read flag for server logs being fetched.')
@click.option('-l', '--page-size', type=int, default=20,
              help='Number of logs to fetch (from latest log)')
@click.option('-n', '--page-number', type=int, default=1,
              help='Page number to fetch.')
def list(mark_read, page_size, page_number):
    '''Fetch server (error) logs.'''
    with Session() as session:
        try:
            resp = session.ServerLog.list(mark_read, page_size, page_number)
            logs = resp.get('logs')
            count = resp.get('count', 0)
            if logs is not None:
                for log in logs:
                    log_time = datetime.utcfromtimestamp(log['created_at']).strftime('%Y-%m-%d %H:%M:%S')
                    print('----')
                    print(log_time, log['severity'].upper(), log['source'], log['user'])
                    print(log['request_status'], log['request_url'])
                    print(log['message'])
                    print(log['traceback'])
            else:
                print('No logs.')
        except Exception as e:
            print_error(e)
            sys.exit(1)
