import sys

import click
from tabulate import tabulate

from . import admin
from ...session import Session, is_legacy_server
from ..pretty import print_error


@admin.command()
@click.option('--status', default='RUNNING',
              type=click.Choice(['PREPARING', 'BUILDING', 'RUNNING', 'RESTARTING',
                                 'RESIZING', 'SUSPENDED', 'TERMINATING',
                                 'TERMINATED', 'ERROR', 'ALL']),
              help='Filter by the given status')
@click.option('--access-key', type=str, default=None,
              help='Get sessions for a specific access key '
                   '(only works if you are a super-admin)')
@click.option('--id-only', is_flag=True, help='Display session ids only.')
def sessions(status, access_key, id_only):
    '''
    List and manage compute sessions.
    '''
    fields = [
        ('Session ID', 'sess_id'),
    ]
    if not id_only:
        fields.extend([
            ('Image', 'image'),
            ('Tag', 'tag'),
            ('Created At', 'created_at',),
            ('Terminated At', 'terminated_at'),
            ('Status', 'status'),
            ('Occupied Resource', 'occupied_slots'),
            ('Used Memory (MiB)', 'mem_cur_bytes'),
            ('Max Used Memory (MiB)', 'mem_max_bytes'),
            ('CPU Using (%)', 'cpu_using'),
        ])
        if is_legacy_server():
            del fields[2]

    if access_key is None:
        q = 'query($status:String) {' \
            '  compute_sessions(status:$status) { $fields }' \
            '}'
    else:
        q = 'query($ak:String, $status:String) {' \
            '  compute_sessions(access_key:$ak, status:$status) { $fields }' \
            '}'
    q = q.replace('$fields', ' '.join(item[1] for item in fields))
    v = {
        'status': status if status != 'ALL' else None,
        'ak': access_key,
    }
    with Session() as session:
        try:
            resp = session.Admin.query(q, v)
        except Exception as e:
            print_error(e)
            sys.exit(1)
        if len(resp['compute_sessions']) == 0:
            print('There are no compute sessions currently running.')
            return
        for item in resp['compute_sessions']:
            if 'mem_cur_bytes' in item:
                item['mem_cur_bytes'] = round(item['mem_cur_bytes'] / 2 ** 20, 1)
            if 'mem_max_bytes' in item:
                item['mem_max_bytes'] = round(item['mem_max_bytes'] / 2 ** 20, 1)
        fields = [field for field in fields if field[1]
                  in resp['compute_sessions'][0]]

        if id_only:
            for item in resp['compute_sessions']:
                print(item['sess_id'])
        else:
            print(tabulate((item.values() for item in resp['compute_sessions']),
                           headers=(item[0] for item in fields)))


@admin.command()
@click.argument('sess_id_or_alias', metavar='SESSID')
def session(sess_id_or_alias):
    '''
    Show detailed information for a running compute session.

    SESSID: Session id or its alias.
    '''
    fields = [
        ('Session ID', 'sess_id'),
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
        del fields[3]
    q = 'query($sess_id:String) {' \
        '  compute_session(sess_id:$sess_id) { $fields }' \
        '}'
    q = q.replace('$fields', ' '.join(item[1] for item in fields))
    v = {'sess_id': sess_id_or_alias}
    with Session() as session:
        try:
            resp = session.Admin.query(q, v)
        except Exception as e:
            print_error(e)
            sys.exit(1)
        if resp['compute_session']['sess_id'] is None:
            print('There is no such running compute session.')
            return
        print('Session detail:\n---------------')
        for i, value in enumerate(resp['compute_session'].values()):
            if fields[i][1] in ['mem_cur_bytes', 'mem_max_bytes']:
                value = round(value / 2 ** 20, 1)
            print(fields[i][0] + ': ' + str(value))
