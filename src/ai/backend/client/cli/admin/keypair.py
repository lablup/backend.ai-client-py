import sys

import click

from ai.backend.client.session import Session
from ai.backend.client.output.fields import keypair_fields
from . import admin
from ..pretty import print_done, print_error, print_fail
from ..types import CLIContext


@admin.group()
def keypair() -> None:
    """
    KeyPair administration commands.
    """


@keypair.command()
@click.pass_obj
def info(ctx: CLIContext) -> None:
    """
    Show the server-side information of the currently configured access key.
    """
    fields = [
        keypair_fields['user_id'],
        keypair_fields['full_name'],
        keypair_fields['access_key'],
        keypair_fields['secret_key'],
        keypair_fields['is_active'],
        keypair_fields['is_admin'],
        keypair_fields['created_at'],
        keypair_fields['last_used'],
        keypair_fields['resource_policy'],
        keypair_fields['rate_limit'],
        keypair_fields['concurrency_limit'],
        keypair_fields['concurrency_used'],
    ]
    with Session() as session:
        try:
            kp = session.KeyPair(session.config.access_key)
            item = kp.info(fields=fields)
            ctx.output.print_item(item, fields)
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(1)


@keypair.command()
@click.pass_obj
@click.option('-u', '--user-id', type=str, default=None,
              help='Show keypairs of this given user. [default: show all]')
@click.option('--is-active', type=bool, default=None,
              help='Filter keypairs by activation.')
@click.option('--filter', 'filter_', default=None,
              help='Set the query filter expression.')
@click.option('--order', default=None,
              help='Set the query ordering expression.')
@click.option('--offset', default=0,
              help='The index of the current page start for pagination.')
@click.option('--limit', default=None,
              help='The page size for pagination.')
def list(ctx: CLIContext, user_id, is_active, filter_, order, offset, limit) -> None:
    """
    List keypairs.
    To show all keypairs or other user's, your access key must have the admin
    privilege.
    (admin privilege required)
    """
    fields = [
        keypair_fields['user_id'],
        keypair_fields['full_name'],
        keypair_fields['access_key'],
        keypair_fields['secret_key'],
        keypair_fields['is_active'],
        keypair_fields['is_admin'],
        keypair_fields['created_at'],
        keypair_fields['last_used'],
        keypair_fields['resource_policy'],
        keypair_fields['rate_limit'],
        keypair_fields['concurrency_limit'],
        keypair_fields['concurrency_used'],
    ]
    try:
        with Session() as session:
            fetch_func = lambda pg_offset, pg_size: session.KeyPair.paginated_list(
                is_active,
                user_id=user_id,
                fields=fields,
                page_offset=pg_offset,
                page_size=pg_size,
                filter=filter_,
                order=order,
            )
            ctx.output.print_paginated_list(
                fetch_func,
                initial_page_offset=offset,
                page_size=limit,
            )
    except Exception as e:
        ctx.output.print_error(e)
        sys.exit(1)


@keypair.command()
@click.argument('user-id', type=str, default=None, metavar='USERID')
@click.argument('resource-policy', type=str, default=None, metavar='RESOURCE_POLICY')
@click.option('-a', '--admin', is_flag=True,
              help='Give the admin privilege to the new keypair.')
@click.option('-i', '--inactive', is_flag=True,
              help='Create the new keypair in inactive state.')
@click.option('-r', '--rate-limit', type=int, default=5000,
              help='Set the API query rate limit.')
def add(user_id, resource_policy, admin, inactive,  rate_limit):
    """
    Add a new keypair.

    USER_ID: User ID of a new key pair.
    RESOURCE_POLICY: resource policy for new key pair.
    """
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


@keypair.command()
@click.argument('access_key', type=str, default=None, metavar='ACCESSKEY')
@click.option('--resource-policy', type=str, help='Resource policy for the keypair.')
@click.option('--is-admin', type=bool, help='Set admin privilege.')
@click.option('--is-active', type=bool, help='Set key pair active or not.')
@click.option('-r', '--rate-limit', type=int, help='Set the API query rate limit.')
def update(access_key, resource_policy, is_admin, is_active,  rate_limit):
    """
    Update an existing keypair.

    ACCESS_KEY: Access key of an existing key pair.
    """
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


@keypair.command()
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


@keypair.command()
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


@keypair.command()
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
