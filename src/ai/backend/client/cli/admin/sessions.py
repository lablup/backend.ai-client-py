import sys

import click
from tabulate import tabulate
import textwrap

from . import admin
from ...helper import is_admin
from ...session import Session, is_legacy_server
from ...versioning import get_naming, apply_version_aware_fields
from ..pretty import print_error, print_fail


# Lets say formattable options are:
format_options = {
    'name':            ('Session Name',
                        lambda api_session: get_naming(api_session.api_version, 'name_gql_field')),
    'type':            ('Type',
                        lambda api_session: get_naming(api_session.api_version, 'type_gql_field')),
    'task_id':         ('Task ID', 'id'),
    'kernel_id':       ('Kernel ID', 'id'),
    'status':          ('Status', 'status'),
    'status_info':     ('Status Info', 'status_info'),
    'created_at':      ('Created At', 'created_at'),
    'last_updated':    ('Last updated', 'status_changed'),
    'result':          ('Result', 'result'),
    'owner':           ('Owner', 'access_key'),
    'image':           ('Image', 'image'),
    'tag':             ('Tag', 'tag'),
    'occupied_slots':  ('Occupied Resource', 'occupied_slots'),
    'used_memory':     ('Used Memory (MiB)', 'mem_cur_bytes'),
    'max_used_memory': ('Max Used Memory (MiB)', 'mem_max_bytes'),
    'cpu_using':       ('CPU Using (%)', 'cpu_using'),
}


@admin.command()
@click.option('-s', '--status', default=None,
              type=click.Choice([
                  'PENDING',
                  'PREPARING', 'BUILDING', 'RUNNING', 'RESTARTING',
                  'RESIZING', 'SUSPENDED', 'TERMINATING',
                  'TERMINATED', 'ERROR', 'CANCELLED',
                  'ALL',  # special case
              ]),
              help='Filter by the given status')
@click.option('--access-key', type=str, default=None,
              help='Get sessions for a specific access key '
                   '(only works if you are a super-admin)')
@click.option('--name-only', is_flag=True, help='Display session names only.')
@click.option('--show-tid', is_flag=True, help='Display task/kernel IDs.')
@click.option('--dead', is_flag=True,
              help='Filter only dead sessions. Ignores --status option.')
@click.option('--running', is_flag=True,
              help='Filter only scheduled and running sessions. Ignores --status option.')
@click.option('-a', '--all', is_flag=True,
              help='Display all sessions matching the condition using pagination.')
@click.option('--detail', is_flag=True, help='Show more details using more columns.')
@click.option('-f', '--format', default=None,  help='Display only specified fields.')
@click.option('--plain', is_flag=True,
              help='Display the session list without decorative line drawings and the header.')
def sessions(status, access_key, name_only, show_tid, dead, running, all, detail, plain, format):
    '''
    List and manage compute sessions.
    '''
    fields = []
    try:
        with Session() as session:
            name_key = get_naming(session.api_version, 'name_gql_field')
            fields.append(format_options['name'])
            if is_admin(session) and not is_legacy_server():
                fields.append(format_options['owner'])
    except Exception as e:
        print_error(e)
        sys.exit(1)
    if name_only:
        pass
    elif format is not None:
        options = format.split(',')
        for opt in options:
            if opt not in format_options:
                print_fail(f'There is no such format option: {opt}')
                sys.exit(1)
        fields = [
            format_options[opt] for opt in options
        ]
    else:
        fields.extend([
            format_options['image'],
            format_options['type'],
            format_options['status'],
            format_options['status_info'],
            format_options['last_updated'],
            format_options['result'],
        ])
        if show_tid:
            fields.insert(
                2,
                format_options['task_id'])
        if detail:
            fields.extend([
                format_options['tag'],
                format_options['created_at'],
                format_options['occupied_slots'],
                format_options['used_memory'],
                format_options['max_used_memory'],
                format_options['cpu_using'],
            ])

    no_match_name = None
    if status is None:
        status = 'PENDING,PREPARING,PULLING,RUNNING,RESTARTING,TERMINATING,RESIZING,SUSPENDED,ERROR'
        no_match_name = 'active'
    if running:
        status = 'PREPARING,PULLING,RUNNING'
        no_match_name = 'running'
    if dead:
        status = 'CANCELLED,TERMINATED'
        no_match_name = 'dead'
    if status == 'ALL':
        status = ('PENDING,PREPARING,PULLING,RUNNING,RESTARTING,TERMINATING,RESIZING,SUSPENDED,ERROR,'
                  'CANCELLED,TERMINATED')
        no_match_name = 'in any status'
    if no_match_name is None:
        no_match_name = status.lower()

    def execute_paginated_query(limit, offset):
        nonlocal fields
        q = '''
        query($limit:Int!, $offset:Int!, $ak:String, $status:String) {
          compute_session_list(
              limit:$limit, offset:$offset, access_key:$ak, status:$status) {
            items { $fields }
            total_count
          }
        }'''
        q = textwrap.dedent(q).strip()
        q = q.replace('$fields', ' '.join(item[1] for item in fields))
        v = {
            'limit': limit,
            'offset': offset,
            'status': status,
            'ak': access_key,
        }
        try:
            resp = session.Admin.query(q, v)
        except Exception as e:
            print_error(e)
            sys.exit(1)
        return resp['compute_session_list']

    def round_mem(items):
        for item in items:
            if 'mem_cur_bytes' in item:
                item['mem_cur_bytes'] = round(item['mem_cur_bytes'] / 2 ** 20, 1)
            if 'mem_max_bytes' in item:
                item['mem_max_bytes'] = round(item['mem_max_bytes'] / 2 ** 20, 1)
        return items

    def _generate_paginated_results(interval):
        nonlocal fields
        offset = 0
        is_first = True
        total_count = -1
        while True:
            limit = (interval if is_first else
                    min(interval, total_count - offset))
            try:
                result = execute_paginated_query(limit, offset)
            except Exception as e:
                print_error(e)
                sys.exit(1)
            offset += interval
            total_count = result['total_count']
            items = result['items']
            items = round_mem(items)

            if name_only:
                yield '\n'.join([item[name_key] for item in items]) + '\n'
            else:
                table = tabulate(
                    [item.values() for item in items],
                    headers=[] if plain else (item[0] for item in fields),
                    tablefmt="plain" if plain else None
                )
                if not is_first:
                    table_rows = table.split('\n')
                    table = '\n'.join(table_rows[2:])
                yield table + '\n'

            if is_first:
                is_first = False
            if not offset < total_count:
                break

    with Session() as session:
        fields = apply_version_aware_fields(session, fields)
        paginating_interval = 10
        try:
            if all:
                click.echo_via_pager(_generate_paginated_results(paginating_interval))
            else:
                result = execute_paginated_query(paginating_interval, offset=0)
                total_count = result['total_count']
                if total_count == 0:
                    print('There are no compute sessions currently {0}.'
                          .format(no_match_name))
                    return
                items = result['items']
                items = round_mem(items)
                if name_only:
                    for item in items:
                        print(item[name_key])
                else:
                    print(tabulate([item.values() for item in items],
                                    headers=[] if plain else (item[0] for item in fields),
                                    tablefmt="plain" if plain else None))
                if total_count > paginating_interval:
                    print("More sessions can be displayed by using -a/--all option.")
        except Exception as e:
            print_error(e)
            sys.exit(1)


@admin.command()
@click.argument('name', metavar='NAME')
def session(name):
    '''
    Show detailed information for a running compute session.

    SESSID: Session id or its alias.
    '''
    fields = [
        ('Session Name', lambda api_session: get_naming(api_session.api_version, 'name_gql_field')),
        ('Session Type', lambda api_session: get_naming(api_session.api_version, 'type_gql_field')),
        ('Role', 'role'),
        ('Image', 'image'),
        ('Tag', 'tag'),
        ('Created At', 'created_at'),
        ('Terminated At', 'terminated_at'),
        ('Agent', 'agent'),
        ('Status', 'status'),
        ('Status Info', 'status_info'),
        ('Occupied Resources', 'occupied_slots'),
        ('CPU Used (ms)', 'cpu_used'),
        ('Used Memory (MiB)', 'mem_cur_bytes'),
        ('Max Used Memory (MiB)', 'mem_max_bytes'),
        ('Number of Queries', 'num_queries'),
        ('Network RX Bytes', 'net_rx_bytes'),
        ('Network TX Bytes', 'net_tx_bytes'),
        ('IO Read Bytes', 'io_read_bytes'),
        ('IO Write Bytes', 'io_write_bytes'),
        ('IO Max Scratch Size', 'io_max_scratch_size'),
        ('IO Current Scratch Size', 'io_cur_scratch_size'),
        ('CPU Using (%)', 'cpu_using'),
    ]
    if is_legacy_server():
        del fields[4]  # tag
    with Session() as session:
        fields = apply_version_aware_fields(session, fields)
        name_key = get_naming(session, 'name_gql_field')
        q = 'query($name: String!) {' \
            f'  compute_session({name_key}: $name) {{ $fields }}' \
            '}'
        q = q.replace('$fields', ' '.join(item[1] for item in fields))
        name_key = get_naming(session.api_version, 'name_gql_field')
        v = {name_key: name}
        try:
            resp = session.Admin.query(q, v)
        except Exception as e:
            print_error(e)
            sys.exit(1)
        if resp['compute_session'][name_key] is None:
            print('There is no such running compute session.')
            return
        print('Session detail:\n---------------')
        for i, value in enumerate(resp['compute_session'].values()):
            if fields[i][1] in ['mem_cur_bytes', 'mem_max_bytes']:
                value = round(value / 2 ** 20, 1)
            print(fields[i][0] + ': ' + str(value))
