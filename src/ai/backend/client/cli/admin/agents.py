import sys

import click
from tabulate import tabulate

from . import admin
from ...session import Session, is_legacy_server
from ..pretty import print_error


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
            agent = session.Agent(agent_id)
            info = agent.info(fields=(item[1] for item in fields))
        except Exception as e:
            print_error(e)
            sys.exit(1)
        rows = []
        for name, key in fields:
            if key == 'mem_cur_bytes' and info[key] is not None:
                info[key] = round(info[key] / 2 ** 20, 1)
            if key in info:
                rows.append((name, info[key]))
        print(tabulate(rows, headers=('Field', 'Value')))


@admin.command()
@click.option('-s', '--status', type=str, default='ALIVE',
              help='Filter agents by the given status.')
def agents(status):
    '''
    List and manage agents.
    (admin privilege required)
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
            items = session.Agent.list(status, fields=(item[1] for item in fields))
        except Exception as e:
            print_error(e)
            sys.exit(1)
        if len(items) == 0:
            print('There are no matching agents.')
            return
        for item in items:
            if 'mem_cur_bytes' in item and item['mem_cur_bytes'] is not None:
                item['mem_cur_bytes'] = round(item['mem_cur_bytes'] / 2 ** 20, 1)
        fields = [field for field in fields if field[1] in items[0]]
        print(tabulate((item.values() for item in items),
                       headers=(item[0] for item in fields)))
