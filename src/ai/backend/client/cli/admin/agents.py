import json
import sys

import click
import humanize
from tabulate import tabulate

from . import admin
from ...session import Session, is_legacy_server
from ..pretty import print_error
from ..pagination import (
    get_preferred_page_size,
    echo_via_pager,
    tabulate_items,
)
from ..utils import format_nested_dicts
from ...exceptions import NoItems


def format_stats(raw_stats):

    value_formatters = {
        'bytes': lambda m: "{} / {}".format(
            humanize.naturalsize(int(m['current']), binary=True),
            humanize.naturalsize(int(m['capacity']), binary=True),
        ),
        'Celsius': lambda m: "{:,} C".format(
            float(m['current']),
        ),
        'bps': lambda m: "{}/s".format(
            humanize.naturalsize(float(m['current'])),
        ),
        'pct': lambda m: "{} %".format(
            m['pct'],
        ),
    }

    def format_value(metric):
        formatter = value_formatters.get(
            metric['unit_hint'],
            lambda m: "{} / {} {}".format(
                m['current'],
                m['capacity'],
                m['unit_hint'],
            ),
        )
        return formatter(metric)

    bufs = []
    node_metric_bufs = []
    for stat_key, metric in raw_stats['node'].items():
        if stat_key == 'cpu_util':
            num_cores = len(raw_stats['devices']['cpu_util'])
            if metric['pct'] is None:
                node_metric_bufs.append(f"{stat_key}: (calculating...) % ({num_cores} cores)")
            else:
                node_metric_bufs.append(f"{stat_key}: {metric['pct']} % ({num_cores} cores)")
        else:
            node_metric_bufs.append(f"{stat_key}: {format_value(metric)}")
    bufs.append(", ".join(node_metric_bufs))
    dev_metric_bufs = []
    for stat_key, per_dev_metric in raw_stats['devices'].items():
        dev_metric_bufs.append(f"+ {stat_key}")
        if stat_key == 'cpu_util' and len(per_dev_metric) > 8:
            dev_metric_bufs.append("  - (per-core stats hidden for large CPUs with more than 8 cores)")
        else:
            for dev_id, metric in per_dev_metric.items():
                dev_metric_bufs.append(
                    f"  - {dev_id}: {format_value(metric)}"
                )
    bufs.append("\n".join(dev_metric_bufs))
    return '\n'.join(bufs)


@admin.command()
@click.argument('agent_id')
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
        ('Total slots', 'available_slots'),
        ('Occupied slots', 'occupied_slots'),
        ('Hardware Metadata', 'hardware_metadata'),
        ('Live Stat', 'live_stat'),
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
                if key == 'live_stat' and resp[key] is not None:
                    rows.append((name, format_stats(json.loads(resp[key]))))
                elif key == 'hardware_metadata':
                    rows.append((name, format_nested_dicts(json.loads(resp[key]))))
                else:
                    rows.append((name, resp[key]))
        print(tabulate(rows, headers=('Field', 'Value')))


@admin.command()
@click.option('-s', '--status', type=str, default='ALIVE',
              help='Filter agents by the given status.')
@click.option('--scaling-group', '--sgroup', type=str, default=None,
              help='Filter agents by the scaling group.')
@click.option('--filter', 'filter_', default=None,
              help='Set the query filter expression.')
@click.option('--order', default=None,
              help='Set the query ordering expression.')
def agents(status, scaling_group, filter_, order):
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
                    filter=filter_,
                    order=order,
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
