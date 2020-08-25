import sys

import click
import humanize
from tabulate import tabulate

from . import admin
from ...session import Session
from ..pretty import print_error


@admin.group(invoke_without_command=True)
@click.pass_context
@click.option('--access-key', type=str, default=None,
              help='Get vfolders for the given access key '
                   '(only works if you are a super-admin)')
def vfolders(ctx, access_key):
    '''
    List and manage virtual folders.
    '''
    if ctx.invoked_subcommand is not None:
        return

    fields = [
        ('Name', 'name'),
        ('Created At', 'created_at'),
        ('Last Used', 'last_used'),
        ('Max Files', 'max_files'),
        ('Max Size', 'max_size'),
    ]
    if access_key is None:
        q = 'query { vfolders { $fields } }'
    else:
        q = 'query($ak:String) { vfolders(access_key:$ak) { $fields } }'
    q = q.replace('$fields', ' '.join(item[1] for item in fields))
    v = {'ak': access_key}
    with Session() as session:
        try:
            resp = session.Admin.query(q, v)
        except Exception as e:
            print_error(e)
            sys.exit(1)
        print(tabulate((item.values() for item in resp['vfolders']),
                       headers=(item[0] for item in fields)))


@vfolders.command()
def list_hosts():
    '''
    List all mounted hosts from virtual folder root.
    (superadmin privilege required)
    '''
    with Session() as session:
        try:
            resp = session.VFolder.list_all_hosts()
            print("Default vfolder host: {}".format(resp['default']))
            print("Mounted hosts: {}".format(', '.join(resp['allowed'])))
        except Exception as e:
            print_error(e)
            sys.exit(1)


@vfolders.command()
@click.argument('vfolder_host')
def perf_metric(vfolder_host):
    '''
    Show the performance statistics of a vfolder host.
    (superadmin privilege required)

    A vfolder host consists of a string of the storage proxy name and the volume name
    separated by a colon. (e.g., "local:volume1")
    '''
    with Session() as session:
        try:
            resp = session.VFolder.get_performance_metric(vfolder_host)
            print(tabulate(
                [(k, humanize.naturalsize(v, binary=True) if 'bytes' in k else f"{v:.2f}")
                 for k, v in resp['metric'].items()],
                headers=('Key', 'Value'),
            ))
        except Exception as e:
            print_error(e)
            sys.exit(1)


@vfolders.command()
@click.option('-a', '--agent-id', type=str, default=None,
              help='Target agent to fetch fstab contents.')
def get_fstab_contents(agent_id):
    '''
    Get contents of fstab file from a node.
    (superadmin privilege required)

    If agent-id is not specified, manager's fstab contents will be returned.
    '''
    with Session() as session:
        try:
            resp = session.VFolder.get_fstab_contents(agent_id)
        except Exception as e:
            print_error(e)
            sys.exit(1)
        print(resp)


@vfolders.command()
def list_mounts():
    '''
    List all mounted hosts in virtual folder root.
    (superadmin privilege required)
    '''
    with Session() as session:
        try:
            resp = session.VFolder.list_mounts()
        except Exception as e:
            print_error(e)
            sys.exit(1)
        print('manager')
        for k, v in resp['manager'].items():
            print(' ', k, ':', v)
        print('\nagents')
        for aid, data in resp['agents'].items():
            print(' ', aid)
            for k, v in data.items():
                print('   ', k, ':', v)


@vfolders.command()
@click.argument('fs-location', type=str)
@click.argument('name', type=str)
@click.option('-o', '--options', type=str, default=None, help='Mount options.')
@click.option('--edit-fstab', is_flag=True,
              help='Edit fstab file to mount permanently.')
def mount_host(fs_location, name, options, edit_fstab):
    '''
    Mount a host in virtual folder root.
    (superadmin privilege required)

    \b
    FS-LOCATION: Location of file system to be mounted.
    NAME: Name of mounted host.
    '''
    with Session() as session:
        try:
            resp = session.VFolder.mount_host(name, fs_location, options, edit_fstab)
        except Exception as e:
            print_error(e)
            sys.exit(1)
        print('manager')
        for k, v in resp['manager'].items():
            print(' ', k, ':', v)
        print('agents')
        for aid, data in resp['agents'].items():
            print(' ', aid)
            for k, v in data.items():
                print('   ', k, ':', v)


@vfolders.command()
@click.argument('name', type=str)
@click.option('--edit-fstab', is_flag=True,
              help='Edit fstab file to mount permanently.')
def umount_host(name, edit_fstab):
    '''
    Unmount a host from virtual folder root.
    (superadmin privilege required)

    \b
    NAME: Name of mounted host.
    '''
    with Session() as session:
        try:
            resp = session.VFolder.umount_host(name, edit_fstab)
        except Exception as e:
            print_error(e)
            sys.exit(1)
        print('manager')
        for k, v in resp['manager'].items():
            print(' ', k, ':', v)
        print('agents')
        for aid, data in resp['agents'].items():
            print(' ', aid)
            for k, v in data.items():
                print('   ', k, ':', v)
