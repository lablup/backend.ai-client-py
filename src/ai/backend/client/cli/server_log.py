from datetime import datetime
import json
from pathlib import Path
import sys

import click
from tabulate import tabulate

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
            # if not resp:
            #     print('There is no virtual folders created yet.')
            #     return
            # rows = (tuple(vf[key] for _, key in fields) for vf in resp)
            # hdrs = (display_name for display_name, _ in fields)
            # print(tabulate(rows, hdrs))
            print(resp)
        except Exception as e:
            print_error(e)
            sys.exit(1)
