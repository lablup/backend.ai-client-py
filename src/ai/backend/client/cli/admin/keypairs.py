import sys

import click
from tabulate import tabulate

from . import admin
from ...session import Session
from ..pretty import print_done, print_error, print_fail
from ..pagination import (
    get_preferred_page_size,
    echo_via_pager,
    tabulate_items,
)
from ...exceptions import NoItems


@admin.command()
def keypair():
    '''
    Show the server-side information of the currently configured access key.
    '''
    fields = [
        ('Email', 'user_id'),
        ('Full Name', 'user_info { full_name }'),
        ('Access Key', 'access_key'),
        ('Secret Key', 'secret_key'),
        ('Active?', 'is_active'),
        ('Admin?', 'is_admin'),
        ('Created At', 'created_at'),
        ('Last Used', 'last_used'),
        ('Res.Policy', 'resource_policy'),
        ('Rate Limit', 'rate_limit'),
        ('Concur.Limit', 'concurrency_limit'),
        ('Concur.Used', 'concurrency_used'),
    ]
    with Session() as session:
        try:
            kp = session.KeyPair(session.config.access_key)
            info = kp.info(fields=(item[1] for item in fields))
        except Exception as e:
            print_error(e)
            sys.exit(1)
        rows = []
        for name, key in fields:
            if key.startswith('user_info '):
                full_name = info['user_info'].get('full_name', '')
                rows.append((name, full_name))
            else:
                rows.append((name, info[key]))
        print(tabulate(rows, headers=('Field', 'Value')))


@admin.group(invoke_without_command=True)
@click.pass_context
@click.option('-u', '--user-id', type=str, default=None,
              help='Show keypairs of this given user. [default: show all]')
@click.option('--is-active', type=bool, default=None,
              help='Filter keypairs by activation.')
def keypairs(ctx, user_id, is_active):
    '''
    List and manage keypairs.
    To show all keypairs or other user's, your access key must have the admin
    privilege.
    (admin privilege required)
    '''
    if ctx.invoked_subcommand is not None:
        return
    fields = [
        ('Email', 'user_id'),
        ('Full Name', 'user_info { full_name }'),
        ('Access Key', 'access_key'),
        ('Secret Key', 'secret_key'),
        ('Active?', 'is_active'),
        ('Admin?', 'is_admin'),
        ('Created At', 'created_at'),
        ('Last Used', 'last_used'),
        ('Res.Policy', 'resource_policy'),
        ('Rate Limit', 'rate_limit'),
        ('Concur.Limit', 'concurrency_limit'),
        ('Concur.Used', 'concurrency_used'),
    ]
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        pass  # string-based user ID for Backend.AI v1.4+

    def format_item(item):
        full_name = item['user_info'].get('full_name', '')
        item['user_info'] = full_name

    try:
        with Session() as session:
            page_size = get_preferred_page_size()
            try:
                items = session.KeyPair.paginated_list(
                    is_active,
                    fields=[f[1] for f in fields],
                    page_size=page_size,
                )
                echo_via_pager(
                    tabulate_items(items, fields, item_formatter=format_item)
                )
            except NoItems:
                print("There are no matching keypairs.")
    except Exception as e:
        print_error(e)
        sys.exit(1)


@keypairs.command()
@click.argument('user-id', type=str, default=None, metavar='USERID')
@click.argument('resource-policy', type=str, default=None, metavar='RESOURCE_POLICY')
@click.option('-a', '--admin', is_flag=True,
              help='Give the admin privilege to the new keypair.')
@click.option('-i', '--inactive', is_flag=True,
              help='Create the new keypair in inactive state.')
@click.option('-r', '--rate-limit', type=int, default=5000,
              help='Set the API query rate limit.')
def add(user_id, resource_policy, admin, inactive,  rate_limit):
    '''
    Add a new keypair.

    USER_ID: User ID of a new key pair.
    RESOURCE_POLICY: resource policy for new key pair.
    '''
    try:
        user_id = int(user_id)
    except ValueError:
        pass  # string-based user ID for Backend.AI v1.4+
    with Session() as session:
        try:
            data = session.KeyPair.create(
                user_id,
                is_active=not inactive,
                is_admin=admin,
                resource_policy=resource_policy,
                rate_limit=rate_limit)
        except Exception as e:
            print_error(e)
            sys.exit(1)
        if not data['ok']:
            print_fail('KeyPair creation has failed: {0}'.format(data['msg']))
            sys.exit(1)
        item = data['keypair']
        print('Access Key: {0}'.format(item['access_key']))
        print('Secret Key: {0}'.format(item['secret_key']))


@keypairs.command()
@click.argument('access_key', type=str, default=None, metavar='ACCESSKEY')
@click.option('--resource-policy', type=str, help='Resource policy for the keypair.')
@click.option('--is-admin', type=bool, help='Set admin privilege.')
@click.option('--is-active', type=bool, help='Set key pair active or not.')
@click.option('-r', '--rate-limit', type=int, help='Set the API query rate limit.')
def update(access_key, resource_policy, is_admin, is_active,  rate_limit):
    '''
    Update an existing keypair.

    ACCESS_KEY: Access key of an existing key pair.
    '''
    with Session() as session:
        try:
            data = session.KeyPair.update(
                access_key,
                is_active=is_active,
                is_admin=is_admin,
                resource_policy=resource_policy,
                rate_limit=rate_limit)
        except Exception as e:
            print_error(e)
            sys.exit(1)
        if not data['ok']:
            print_fail('KeyPair update has failed: {0}'.format(data['msg']))
            sys.exit(1)
        print_done('Key pair is updated: ' + access_key + '.')


@keypairs.command()
@click.argument('access-key', type=str, metavar='ACCESSKEY')
def delete(access_key):
    """
    Delete an existing keypair.

    ACCESSKEY: ACCESSKEY for a keypair to delete.
    """
    with Session() as session:
        try:
            data = session.KeyPair.delete(access_key)
        except Exception as e:
            print_error(e)
            sys.exit(1)
        if not data['ok']:
            print_fail('KeyPair deletion has failed: {0}'.format(data['msg']))
            sys.exit(1)
        print_done('Key pair is deleted: ' + access_key + '.')


@keypairs.command()
@click.argument('access-key', type=str, metavar='ACCESSKEY')
def activate(access_key):
    """
    Activate an inactivated keypair.

    ACCESS_KEY: Access key of an existing key pair.
    """
    with Session() as session:
        try:
            data = session.KeyPair.activate(access_key)
        except Exception as e:
            print_error(e)
            sys.exit(1)
        if not data['ok']:
            print_fail('KeyPair activation has failed: {0}'.format(data['msg']))
            sys.exit(1)
        print_done('Key pair is activated: ' + access_key + '.')


@keypairs.command()
@click.argument('access-key', type=str, metavar='ACCESSKEY')
def deactivate(access_key):
    """
    Deactivate an active keypair.

    ACCESS_KEY: Access key of an existing key pair.
    """
    with Session() as session:
        try:
            data = session.KeyPair.deactivate(access_key)
        except Exception as e:
            print_error(e)
            sys.exit(1)
        if not data['ok']:
            print_fail('KeyPair deactivation has failed: {0}'.format(data['msg']))
            sys.exit(1)
        print_done('Key pair is deactivated: ' + access_key + '.')
