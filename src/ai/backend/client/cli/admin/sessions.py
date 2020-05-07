import shutil
import sys
from typing import (
    Any,
    Iterable,
    Dict,
)

import click
from tabulate import tabulate

from . import admin
from ...session import Session
from ...versioning import get_naming, apply_version_aware_fields
from ..pretty import print_error, print_fail
from ..pagination import (
    MAX_PAGE_SIZE,
    execute_paginated_query,
    generate_paginated_results,
    echo_via_pager,
)


SessionItem = Dict[str, Any]


# Lets say formattable options are:
format_options = {
    'name':            ('Session Name',
                        lambda api_session: get_naming(api_session.api_version, 'name_gql_field')),
    'type':            ('Type',
                        lambda api_session: get_naming(api_session.api_version, 'type_gql_field')),
    'task_id':         ('Task/Kernel ID', 'id'),
    'status':          ('Status', 'status'),
    'status_info':     ('Status Info', 'status_info'),
    'created_at':      ('Created At', 'created_at'),
    'last_updated':    ('Last updated', 'status_changed'),
    'result':          ('Result', 'result'),
    'owner':           ('Owner', 'access_key'),
    'image':           ('Image', 'image'),
    'tag':             ('Tag', 'tag'),
    'occupied_slots':  ('Occupied Resource', 'occupied_slots'),
}

format_options_legacy = {
    'used_memory':     ('Used Memory (MiB)', 'mem_cur_bytes'),
    'max_used_memory': ('Max Used Memory (MiB)', 'mem_max_bytes'),
    'cpu_using':       ('CPU Using (%)', 'cpu_using'),
}


def transform_legacy_mem_fields(item: SessionItem) -> SessionItem:
    if 'mem_cur_bytes' in item:
        item['mem_cur_bytes'] = round(item['mem_cur_bytes'] / 2 ** 20, 1)
    if 'mem_max_bytes' in item:
        item['mem_max_bytes'] = round(item['mem_max_bytes'] / 2 ** 20, 1)
    return item


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
def sessions(status, access_key, name_only, dead, running, all, detail, plain, format):
    '''
    List and manage compute sessions.
    '''
    fields = []
    with Session() as session:
        is_admin = session.KeyPair(session.config.access_key).info()['is_admin']
        try:
            name_key = get_naming(session.api_version, 'name_gql_field')
            fields.append(format_options['name'])
            if is_admin:
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
                format_options['task_id'],
                format_options['image'],
                format_options['type'],
                format_options['status'],
                format_options['status_info'],
                format_options['last_updated'],
                format_options['result'],
            ])
            if detail:
                fields.extend([
                    format_options['tag'],
                    format_options['created_at'],
                    format_options['occupied_slots'],
                ])
                if session.api_version[0] < 5:
                    fields.extend([
                        format_options_legacy['used_memory'],
                        format_options_legacy['max_used_memory'],
                        format_options_legacy['cpu_using'],
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

    def format_items(
        items: Iterable[SessionItem],
        page_size: int,
    ) -> Iterable[str]:
        is_first = True
        items = (transform_legacy_mem_fields(item) for item in items)
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
                        headers=[] if plain else [item[0] for item in fields],
                        tablefmt='plain' if plain else 'simple'
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
            # let the page size be same to the terminal height.
            page_size = min(MAX_PAGE_SIZE, shutil.get_terminal_size((80, 20)).lines)
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
                # use a reasonably small page size, considering the heights of
                # table header and shell prompts.
                page_size = max(10, page_size - 6)
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
                    print("More compute sessions can be displayed by using -a/--all option.")
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
        ('Session Name', lambda api_session: get_naming(
            api_session.api_version, 'name_gql_field',
        )),
        ('Session Type', lambda api_session: get_naming(
            api_session.api_version, 'type_gql_field',
        )),
        ('Image', 'image'),
        ('Tag', 'tag'),
        ('Created At', 'created_at'),
        ('Terminated At', 'terminated_at'),
        ('Status', 'status'),
        ('Status Info', 'status_info'),
        ('Occupied Resources', 'occupied_slots'),
    ]
    # fields_legacy = [
    #     ('CPU Used (ms)', 'cpu_used'),
    #     ('Used Memory (MiB)', 'mem_cur_bytes'),
    #     ('Max Used Memory (MiB)', 'mem_max_bytes'),
    #     ('Number of Queries', 'num_queries'),
    #     ('Network RX Bytes', 'net_rx_bytes'),
    #     ('Network TX Bytes', 'net_tx_bytes'),
    #     ('IO Read Bytes', 'io_read_bytes'),
    #     ('IO Write Bytes', 'io_write_bytes'),
    #     ('IO Max Scratch Size', 'io_max_scratch_size'),
    #     ('IO Current Scratch Size', 'io_cur_scratch_size'),
    #     ('CPU Using (%)', 'cpu_using'),
    # ]
    with Session() as session:
        if session.api_version < (4, '20181215'):
            del fields[4]  # tag
        fields = apply_version_aware_fields(session, fields)
        if session.api_version[0] < 5:
            q = f'query($name: String!) {{' \
                f'  compute_session(sess_id: $name) {{ $fields }}' \
                f'}}'
            v = {'name': name}
        else:
            q = 'query($id: UUID!) {' \
                '  compute_session(id: $id) {' \
                '    $fields' \
                '    containers {' \
                '      id agent occupied_slots status status_changed' \
                '    }' \
                '    dependencies {' \
                '      name id status status_changed' \
                '    }' \
                '  }' \
                '}'
            v = {'id': name}
        q = q.replace('$fields', ' '.join(item[1] for item in fields))
        name_key = get_naming(session.api_version, 'name_gql_field')
        try:
            resp = session.Admin.query(q, v)
        except Exception as e:
            print_error(e)
            sys.exit(1)
        if resp['compute_session'][name_key] is None:
            print('There is no such running compute session.')
            return
        transform_legacy_mem_fields(resp['compute_session'])
        for i, value in enumerate(resp['compute_session'].values()):
            if i < len(fields):
                print(fields[i][0] + ': ' + str(value))
        containers_summary = "- " + "\n- ".join(map(repr, resp['compute_session']['containers']))
        if len(resp['compute_session']['dependencies']) == 0:
            dependencies_summary = "- (There are no dependency tasks)"
        else:
            dependencies_summary = "- " + "\n- ".join(map(repr, resp['compute_session']['dependencies']))
        print(f"Containers:\n{containers_summary}")
        print(f"Dependencies:\n{dependencies_summary}")
