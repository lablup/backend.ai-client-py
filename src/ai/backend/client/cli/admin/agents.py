import sys

import click
from tabulate import tabulate

from . import admin
from ...session import Session, is_legacy_server
from ..pretty import print_error
from ..pagination import (
    get_preferred_page_size,
    echo_via_pager,
    tabulate_items,
)
from ...exceptions import NoItems


@admin.command()
@click.option('-i', '--id', 'agent_id', required=True,
              help='The agent Id to inspect.')
def agent(agent_id):
    '''
    Show the information about the given agent.
    '''
    fields = [
        ('ID', 'id'),
        ('Status', 'status'),
        ('Region', 'region'),
        ('First Contact', 'first_contact'),
        ('CPU Usage (%)', 'cpu_cur_pct'),
        ('Used Memory (MiB)', 'mem_cur_bytes'),
        ('Total slots', 'available_slots'),
        ('Occupied slots', 'occupied_slots'),
    ]
    if is_legacy_server():
        del fields[9]
        del fields[6]
    with Session() as session:
        try:
            resp = session.Agent.detail(agent_id=agent_id,
                                        fields=(item[1] for item in fields))
        except Exception as e:
            print_error(e)
            sys.exit(1)
        rows = []
        for name, key in fields:
            if key == 'mem_cur_bytes' and resp[key] is not None:
                resp[key] = round(resp[key] / 2 ** 20, 1)
            if key in resp:
                rows.append((name, resp[key]))
        print(tabulate(rows, headers=('Field', 'Value')))


@admin.command()
@click.option('-s', '--status', type=str, default='ALIVE',
              help='Filter agents by the given status.')
@click.option('--scaling-group', '--sgroup', type=str, default=None,
              help='Filter agents by the scaling group.')
def agents(status, scaling_group):
    '''
    List and manage agents.
    (super-admin privilege required)
    '''
    fields = [
        ('ID', 'id'),
        ('Status', 'status'),
        ('Scaling Group', 'scaling_group'),
        ('Region', 'region'),
        ('First Contact', 'first_contact'),
        ('CPU Usage (%)', 'cpu_cur_pct'),
        ('Used Memory (MiB)', 'mem_cur_bytes'),
        ('Total slots', 'available_slots'),
        ('Occupied slots', 'occupied_slots'),
    ]

    def format_item(item):
        if 'mem_cur_bytes' in item and item['mem_cur_bytes'] is not None:
            item['mem_cur_bytes'] = round(item['mem_cur_bytes'] / 2 ** 20, 1)

    try:
        if is_legacy_server():
            del fields[9]
            del fields[6]
        with Session() as session:
            page_size = get_preferred_page_size()
            try:
                items = session.Agent.paginated_list(
                    status,
                    scaling_group,
                    fields=[f[1] for f in fields],
                    page_size=page_size,
                )
                echo_via_pager(
                    tabulate_items(items, fields,
                                   item_formatter=format_item)
                )
            except NoItems:
                print("There are no matching agents.")
    except Exception as e:
        print_error(e)
        sys.exit(1)


@admin.group()
def watcher():
    '''Provides agent watcher operations.

    Watcher operations are available only for Linux distributions.
    '''


@watcher.command()
@click.argument('agent', type=str)
def status(agent):
    '''
    Get agent and watcher status.
    (superadmin privilege required)

    \b
    AGENT: Agent id.
    '''
    with Session() as session:
        try:
            status = session.AgentWatcher.get_status(agent)
            print(status)
        except Exception as e:
            print_error(e)
            sys.exit(1)


@watcher.command()
@click.argument('agent', type=str)
def agent_start(agent):
    '''
    Start agent service.
    (superadmin privilege required)

    \b
    AGENT: Agent id.
    '''
    with Session() as session:
        try:
            status = session.AgentWatcher.agent_start(agent)
            print(status)
        except Exception as e:
            print_error(e)
            sys.exit(1)


@watcher.command()
@click.argument('agent', type=str)
def agent_stop(agent):
    '''
    Stop agent service.
    (superadmin privilege required)

    \b
    AGENT: Agent id.
    '''
    with Session() as session:
        try:
            status = session.AgentWatcher.agent_stop(agent)
            print(status)
        except Exception as e:
            print_error(e)
            sys.exit(1)


@watcher.command()
@click.argument('agent', type=str)
def agent_restart(agent):
    '''
    Restart agent service.
    (superadmin privilege required)

    \b
    AGENT: Agent id.
    '''
    with Session() as session:
        try:
            status = session.AgentWatcher.agent_restart(agent)
            print(status)
        except Exception as e:
            print_error(e)
            sys.exit(1)
