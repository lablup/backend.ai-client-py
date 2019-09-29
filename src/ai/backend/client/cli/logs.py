import asyncio
import sys

import click

from . import main
from .pretty import print_wait, print_done, print_error
from ..session import Session, AsyncSession


@main.command()
@click.argument('sess_id_or_alias', metavar='SESSID')
def logs(sess_id_or_alias):
    '''
    Shows the output logs of a running container.

    \b
    SESSID: Session ID or its alias given when creating the session.
    '''
    with Session() as session:
        try:
            print_wait('Retrieving live container logs...')
            kernel = session.Kernel(sess_id_or_alias)
            result = kernel.get_logs().get('result')
            logs = result.get('logs') if 'logs' in result else ''
            print(logs)
            print_done('End of logs.')
        except Exception as e:
            print_error(e)
            sys.exit(1)


@main.command()
@click.argument('task_id', metavar='TASKID')
def task_logs(task_id):
    '''
    Shows the output logs of a batch task.

    \b
    TASKID: An UUID of a task (or kernel).
    '''
    async def _task_logs():
        async with AsyncSession() as session:
            async for chunk in session.Kernel.get_task_logs(task_id):
                print(chunk.decode('utf8', errors='replace'), end='')

    try:
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(_task_logs())
        finally:
            loop.stop()
    except Exception as e:
        print_error(e)
        sys.exit(1)
