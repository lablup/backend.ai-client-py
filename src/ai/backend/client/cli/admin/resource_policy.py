import sys

import click
from tabulate import tabulate

from . import admin
from ...session import Session
from ..interaction import ask_yn
from ..pretty import print_done, print_error, print_fail, print_info, print_warn


@admin.command()
@click.option('-n', '--name', type=str, default=None,
              help='Name of the resource policy.')
def keypair_resource_policy(name):
    """
    Show details about a keypair resource policy. When `name` option is omitted, the
    resource policy for the current access_key will be returned.
    """
    fields = [
        ('Name', 'name'),
        ('Created At', 'created_at'),
        ('Default for Unspecified', 'default_for_unspecified'),
        ('Total Resource Slot', 'total_resource_slots'),
        ('Max Concurrent Sessions', 'max_concurrent_sessions'),
        ('Max Containers per Session', 'max_containers_per_session'),
        ('Max vFolder Count', 'max_vfolder_count'),
        ('Max vFolder Size', 'max_vfolder_size'),
        ('Idle Timeeout', 'idle_timeout'),
        ('Allowed vFolder Hosts', 'allowed_vfolder_hosts'),
    ]
    with Session() as session:
        try:
            rp = session.KeypairResourcePolicy(session.config.access_key)
            info = rp.info(name, fields=(item[1] for item in fields))
        except Exception as e:
            print_error(e)
            sys.exit(1)
        rows = []
        if info is None:
            print_warn('No such resource policy.')
            sys.exit(1)
        for name, key in fields:
            rows.append((name, info[key]))
        print(tabulate(rows, headers=('Field', 'Value')))


@admin.group(invoke_without_command=True)
@click.pass_context
def keypair_resource_policies(ctx):
    '''
    List and manage keypair resource policies.
    (admin privilege required)
    '''
    if ctx.invoked_subcommand is not None:
        return
    fields = [
        ('Name', 'name'),
        ('Created At', 'created_at'),
        ('Default for Unspecified', 'default_for_unspecified'),
        ('Total Resource Slot', 'total_resource_slots'),
        ('Max Concurrent Sessions', 'max_concurrent_sessions'),
        ('Max Containers per Session', 'max_containers_per_session'),
        ('Max vFolder Count', 'max_vfolder_count'),
        ('Max vFolder Size', 'max_vfolder_size'),
        ('Idle Timeeout', 'idle_timeout'),
        ('Allowed vFolder Hosts', 'allowed_vfolder_hosts'),
    ]
    with Session() as session:
        try:
            items = session.KeypairResourcePolicy.list(fields=(item[1] for item in fields))
        except Exception as e:
            print_error(e)
            sys.exit(1)
        if len(items) == 0:
            print_warn('There are no keypair resource policies.')
            return
        print(tabulate((item.values() for item in items),
                       headers=(item[0] for item in fields)))


@keypair_resource_policies.command()
@click.argument('name', type=str, default=None, metavar='NAME')
@click.option('--default-for-unspecified', type=str, default='UNLIMITED',
              help='Default behavior for unspecified resources: '
                   'LIMITED, UNLIMITED')
@click.option('--total-resource-slots', type=str, default='{}',
              help='Set total resource slots.')
@click.option('--max-concurrent-sessions', type=int, default=30,
              help='Number of maximum concurrent sessions.')
@click.option('--max-containers-per-session', type=int, default=1,
              help='Number of maximum containers per session.')
@click.option('--max-vfolder-count', type=int, default=10,
              help='Number of maximum virtual folders allowed.')
@click.option('--max-vfolder-size', type=int, default=0,
              help='Maximum virtual folder size (future plan).')
@click.option('--idle-timeout', type=int, default=1800,
              help='The maximum period of time allowed for kernels to wait '
                   'further requests.')
# @click.option('--allowed-vfolder-hosts', type=click.Tuple(str), default=['local'],
#               help='Locations to create virtual folders.')
@click.option('--allowed-vfolder-hosts', default=['local'],
              help='Locations to create virtual folders.')
def add(name, default_for_unspecified, total_resource_slots, max_concurrent_sessions,
        max_containers_per_session, max_vfolder_count, max_vfolder_size,
        idle_timeout, allowed_vfolder_hosts):
    '''
    Add a new keypair resource policy.

    NAME: NAME of a new keypair resource policy.
    '''
    with Session() as session:
        try:
            data = session.KeypairResourcePolicy.create(
                name,
                default_for_unspecified=default_for_unspecified,
                total_resource_slots=total_resource_slots,
                max_concurrent_sessions=max_concurrent_sessions,
                max_containers_per_session=max_containers_per_session,
                max_vfolder_count=max_vfolder_count,
                max_vfolder_size=max_vfolder_size,
                idle_timeout=idle_timeout,
                allowed_vfolder_hosts=allowed_vfolder_hosts,
            )
        except Exception as e:
            print_error(e)
            sys.exit(1)
        if not data['ok']:
            print_fail('KeyPair Resource Policy creation has failed: {0}'
                       .format(data['msg']))
            sys.exit(1)
        item = data['resource_policy']
        print_done('Keypair resource policy ' + item['name'] + ' is created.')


@keypair_resource_policies.command()
@click.argument('name', type=str, default=None, metavar='NAME')
@click.option('--default-for-unspecified', type=str,
              help='Default behavior for unspecified resources: '
                   'LIMITED, UNLIMITED')
@click.option('--total-resource-slots', type=str,
              help='Set total resource slots.')
@click.option('--max-concurrent-sessions', type=int,
              help='Number of maximum concurrent sessions.')
@click.option('--max-containers-per-session', type=int,
              help='Number of maximum containers per session.')
@click.option('--max-vfolder-count', type=int,
              help='Number of maximum virtual folders allowed.')
@click.option('--max-vfolder-size', type=int,
              help='Maximum virtual folder size (future plan).')
@click.option('--idle-timeout', type=int,
              help='The maximum period of time allowed for kernels to wait '
                   'further requests.')
@click.option('--allowed-vfolder-hosts', help='Locations to create virtual folders.')
def update(name, default_for_unspecified, total_resource_slots,
           max_concurrent_sessions, max_containers_per_session, max_vfolder_count,
           max_vfolder_size, idle_timeout, allowed_vfolder_hosts):
    """
    Update an existing keypair resource policy.

    NAME: NAME of a keypair resource policy to update.
    """
    with Session() as session:
        try:
            data = session.KeypairResourcePolicy.update(
                name,
                default_for_unspecified=default_for_unspecified,
                total_resource_slots=total_resource_slots,
                max_concurrent_sessions=max_concurrent_sessions,
                max_containers_per_session=max_containers_per_session,
                max_vfolder_count=max_vfolder_count,
                max_vfolder_size=max_vfolder_size,
                idle_timeout=idle_timeout,
                allowed_vfolder_hosts=allowed_vfolder_hosts,
            )
        except Exception as e:
            print_error(e)
            sys.exit(1)
        if not data['ok']:
            print_fail('KeyPair Resource Policy creation has failed: {0}'
                       .format(data['msg']))
            sys.exit(1)
        print_done('Update succeeded.')


@keypair_resource_policies.command()
@click.argument('name', type=str, default=None, metavar='NAME')
def delete(name):
    """
    Delete a keypair resource policy.

    NAME: NAME of a keypair resource policy to delete.
    """
    with Session() as session:
        if not ask_yn():
            print_info('Cancelled.')
            sys.exit(1)
        try:
            data = session.KeypairResourcePolicy.delete(name)
        except Exception as e:
            print_error(e)
            sys.exit(1)
        if not data['ok']:
            print_fail('KeyPair Resource Policy deletion has failed: {0}'
                       .format(data['msg']))
            sys.exit(1)
        print_done('Resource policy ' + name + ' is deleted.')
