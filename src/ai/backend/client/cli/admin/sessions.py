from collections import defaultdict
import functools
import json
import sys
import textwrap
from typing import (
    Any,
    Dict,
    Mapping,
    Optional,
    Sequence,
)
import uuid

import click

from . import admin
from ...session import Session
from ...versioning import get_naming, apply_version_aware_fields
from ..pretty import print_error, print_fail
from ..pagination import (
    get_preferred_page_size,
    echo_via_pager,
    tabulate_items,
)
from ...exceptions import NoItems


SessionItem = Dict[str, Any]


# Lets say formattable options are:
format_options = {
    'name':             ('Session Name',
                         lambda api_session: get_naming(api_session.api_version, 'name_gql_field')),
    'type':             ('Type',
                         lambda api_session: get_naming(api_session.api_version, 'type_gql_field')),
    'kernel_id':        ('Kernel/Task ID', 'id'),
    'session_id':       ('Session ID', 'session_id'),
    'status':           ('Status', 'status'),
    'status_info':      ('Status Info', 'status_info'),
    'created_at':       ('Created At', 'created_at'),
    'terminated_at':    ('Terminated At', 'terminated_at'),
    'last_updated':     ('Last updated', 'status_changed'),
    'result':           ('Result', 'result'),
    'group':            ('Project/Group', 'group_name'),
    'owner':            ('Owner', 'access_key'),
    'image':            ('Image', 'image'),
    'tag':              ('Tag', 'tag'),
    'occupied_slots':   ('Occupied Resource', 'occupied_slots'),
    'cluster_hostname': ('Hostname', 'cluster_hostname'),
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
@click.option('--detail', is_flag=True, help='Show more details using more columns.')
@click.option('-f', '--format', default=None,  help='Display only specified fields.')
@click.option('--plain', is_flag=True,
              help='Display the session list without decorative line drawings and the header.')
def sessions(status, access_key, name_only, dead, running, detail, plain, format):
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
            if session.api_version[0] >= 6:
                fields.append(format_options['session_id'])
            fields.extend([
                format_options['group'],
                format_options['kernel_id'],
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

    try:
        with Session() as session:
            fields = apply_version_aware_fields(session, fields)
            # let the page size be same to the terminal height.
            page_size = get_preferred_page_size()
            try:
                items = session.ComputeSession.paginated_list(
                    status, access_key,
                    fields=[f[1] for f in fields],
                    page_size=page_size,
                )
                if name_only:
                    echo_via_pager(
                        (f"{item[name_key]}\n" for item in items)
                    )
                else:
                    echo_via_pager(
                        tabulate_items(items, fields,
                                       item_formatter=transform_legacy_mem_fields)
                    )
            except NoItems:
                print("There are no matching sessions.")
    except Exception as e:
        print_error(e)
        sys.exit(1)


def format_stats(raw_stats: Optional[str], indent='') -> str:
    if raw_stats is None:
        return "(unavailable)"
    stats = json.loads(raw_stats)
    text = "\n".join(f"- {k + ': ':18s}{v}" for k, v in stats.items())
    return "\n" + textwrap.indent(text, indent)


def format_containers(containers: Sequence[Mapping[str, Any]], indent='') -> str:
    if len(containers) == 0:
        text = "- (There are no sub-containers belonging to the session)"
    else:
        text = ""
        for cinfo in containers:
            text += "\n".join((
                f"+ {cinfo['id']}",
                *(f"  - {k + ': ':18s}{v}"
                  for k, v in cinfo.items()
                  if k not in ('id', 'live_stat', 'last_stat')),
                f"  + live_stat: {format_stats(cinfo['live_stat'], indent='    ')}",
                f"  + last_stat: {format_stats(cinfo['last_stat'], indent='    ')}",
            )) + "\n"
    return "\n" + textwrap.indent(text, indent)


def format_dependencies(dependencies: Sequence[Mapping[str, Any]], indent='') -> str:
    if len(dependencies) == 0:
        text = "- (There are no dependency tasks)"
    else:
        text = ""
        for dinfo in dependencies:
            text += "\n".join(
                (f"+ {dinfo['name']} ({dinfo['id']})",
                *(f"  - {k + ': ':18s}{v}" for k, v in dinfo.items() if k not in ('name', 'id'))),
            )
    return "\n" + textwrap.indent(text, indent)


@admin.command()
@click.argument('id_or_name', metavar='ID_OR_NAME')
def session(id_or_name):
    '''
    Show detailed information for a running compute session.
    '''
    with Session() as session_:
        fields = [
            ('Session Name', lambda api_session: get_naming(
                api_session.api_version, 'name_gql_field',
            )),
        ]
        if session_.api_version[0] >= 6:
            fields.append(format_options['session_id'])
            fields.append(format_options['kernel_id'])
        fields.extend([
            format_options['image'],
        ])
        if session_.api_version >= (4, '20181215'):
            fields.append(format_options['tag'])
        fields.extend([
            format_options['created_at'],
            format_options['terminated_at'],
            format_options['status'],
            format_options['status_info'],
            format_options['occupied_slots'],
        ])
        fields = apply_version_aware_fields(session_, fields)
        field_formatters = defaultdict(lambda: str)
        field_formatters['last_stat'] = format_stats
        field_formatters['containers'] = functools.partial(format_containers, indent='  ')
        field_formatters['dependencies'] = functools.partial(format_dependencies, indent='  ')
        if session_.api_version[0] < 5:
            # In API v4 or older, we can only query a currently running session
            # using its user-defined alias name.
            fields.append(('Last Stats', 'last_stat'))
            q = 'query($name: String!) {' \
                '  compute_session(sess_id: $name) { $fields }' \
                '}'
            v = {'name': id_or_name}
        else:
            # In API v5 or later, we can query any compute session both in the history
            # and currently running using its UUID.
            # NOTE: Partial ID/alias matching is supported in the REST API only.
            if session_.api_version[0] >= 6:
                fields.append((
                    'Containers',
                    'containers {'
                    ' id cluster_role cluster_idx cluster_hostname '
                    ' agent status status_info status_changed '
                    ' occupied_slots live_stat last_stat '
                    '}',
                ))
            else:
                fields.append((
                    'Containers',
                    'containers {'
                    ' id role agent status status_info status_changed '
                    ' occupied_slots live_stat last_stat '
                    '}',
                ))
            fields.append((
                'Dependencies',
                'dependencies { name id status status_info status_changed }',
            ))
            q = 'query($id: UUID!) {' \
                '  compute_session(id: $id) {' \
                '    $fields' \
                '  }' \
                '}'
            try:
                uuid.UUID(id_or_name)
            except ValueError:
                print_fail("In API v5 or later, the session ID must be given in the UUID format.")
                sys.exit(1)
            v = {'id': id_or_name}
        q = q.replace('$fields', ' '.join(item[1] for item in fields))
        try:
            resp = session_.Admin.query(q, v)
        except Exception as e:
            print_error(e)
            sys.exit(1)
        if resp['compute_session'] is None:
            if session_.api_version[0] < 5:
                print_fail('There is no such running compute session.')
            else:
                print_fail('There is no such compute session.')
            sys.exit(1)
        transform_legacy_mem_fields(resp['compute_session'])
        for i, (key, value) in enumerate(resp['compute_session'].items()):
            fmt = field_formatters[key]
            print(f"{fields[i][0] + ': ':20s}{fmt(value)}")
