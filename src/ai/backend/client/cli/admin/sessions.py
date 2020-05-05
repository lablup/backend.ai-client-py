import sys

import click
from tabulate import tabulate

from . import admin
from ...helper import is_admin
from ...session import Session, is_legacy_server
from ...versioning import get_naming, apply_version_aware_fields
from ..pretty import print_error, print_fail
from ..pagination import execute_paginated_query, generate_paginated_results, echo_via_pager


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

    def round_mem(items):
        for item in items:
            if 'mem_cur_bytes' in item:
                item['mem_cur_bytes'] = round(item['mem_cur_bytes'] / 2 ** 20, 1)
            if 'mem_max_bytes' in item:
                item['mem_max_bytes'] = round(item['mem_max_bytes'] / 2 ** 20, 1)
            yield item

    def format_items(items, page_size):
        is_first = True
        items = round_mem(items)
        if name_only:
            for item in items:
                yield item[name_key]
        else:
            output_count = 0
            buffered_items = []
            # If we iterate until the end of items, pausing the terminal output
            # would not have effects for avoiding unnecessary queries for subsequent pages.
            # Let's buffer the items and split the formatting per page.
            for item in items:
                buffered_items.append(item)
                output_count += 1
                if output_count == page_size:
                    table = tabulate(
                        [item.values() for item in buffered_items],
                        headers=[] if plain else (item[0] for item in fields),
                        tablefmt="plain" if plain else None
                    )
                    table_rows = table.splitlines()
                    if is_first:
                        yield from (row + '\n' for row in table_rows)
                    else:
                        # strip the header for continued page outputs
                        yield from (row + '\n' for row in table_rows[2:])
                    buffered_items.clear()
                    is_first = False
                    output_count = 0

    try:
        with Session() as session:
            fields = apply_version_aware_fields(session, fields)
            page_size = 20
            if all:
                echo_via_pager(format_items(generate_paginated_results(
                    session,
                    'compute_session_list',
                    {
                        'status': (status, 'String'),
                        'access_key': (access_key, 'String'),
                    },
                    fields,
                    page_size=page_size,
                ), page_size))
            else:
                result = execute_paginated_query(
                    session,
                    'compute_session_list',
                    {
                        'status': (status, 'String'),
                        'access_key': (access_key, 'String'),
                    },
                    fields,
                    limit=page_size,
                    offset=0,
                )
                total_count = result['total_count']
                if total_count == 0:
                    print('There are no compute sessions currently {0}.'
                          .format(no_match_name))
                    return
                for formatted_line in format_items(result['items'], page_size):
                    click.echo(formatted_line, nl=False)
                if total_count > page_size:
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
