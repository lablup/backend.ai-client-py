import sys

import click
from tabulate import tabulate

from . import admin
from ...session import Session
from ..interaction import ask_yn
from ..pretty import print_error, print_info, print_fail
from ..pagination import (
    get_preferred_page_size,
    echo_via_pager,
    tabulate_items,
)
from ...exceptions import NoItems


@admin.command()
@click.option('-e', '--email', type=str, default=None,
              help='Email of a user to display.')
def user(email):
    '''
    Show the information about the given user by email. If email is not give,
    requester's information will be displayed.
    '''
    fields = [
        ('UUID', 'uuid'),
        ('Username', 'username'),
        ('Role', 'role'),
        ('Email', 'email'),
        ('Name', 'full_name'),
        ('Need Password Change', 'need_password_change'),
        ('Status', 'status'),
        ('Status Info', 'status_info'),
        ('Created At', 'created_at'),
        ('Domain Name', 'domain_name'),
        ('Groups', 'groups { id name }'),
    ]
    with Session() as session:
        try:
            resp = session.User.detail(email=email, fields=(item[1] for item in fields))
        except Exception as e:
            print_error(e)
            sys.exit(1)
        rows = []
        if resp is None:
            print('There is no such user.')
            sys.exit(1)
        for name, key in fields:
            if key.startswith('groups '):
                group_list = [f"{g['name']} ({g['id']})" for g in resp['groups']]
                rows.append((name, ",\n".join(group_list)))
            else:
                rows.append((name, resp[key]))
        print(tabulate(rows, headers=('Field', 'Value')))


@admin.group(invoke_without_command=True)
@click.pass_context
@click.option('-s', '--status', type=str, default=None,
              help='Filter users in a specific state (active, inactive, deleted, before-verification).')
@click.option('-g', '--group', type=str, default=None,
              help='Filter by group ID.')
def users(ctx, status, group) -> None:
    '''
    List and manage users.
    (admin privilege required)
    '''
    if ctx.invoked_subcommand is not None:
        return
    fields = [
        ('UUID', 'uuid'),
        ('Username', 'username'),
        ('Role', 'role'),
        ('Email', 'email'),
        ('Name', 'full_name'),
        ('Need Password Change', 'need_password_change'),
        ('Status', 'status'),
        ('Status Info', 'status_info'),
        ('Created At', 'created_at'),
        ('Domain Name', 'domain_name'),
        ('Groups', 'groups { id name }'),
    ]

    def format_item(item):
        group_list = [g['name'] for g in item['groups']]
        item['groups'] = ", ".join(group_list)

    try:
        with Session() as session:
            page_size = get_preferred_page_size()
            try:
                items = session.User.paginated_list(
                    status, group,
                    fields=[f[1] for f in fields],
                    page_size=page_size,
                )
                echo_via_pager(
                    tabulate_items(items, fields,
                                   item_formatter=format_item)
                )
            except NoItems:
                print("There are no matching users.")
    except Exception as e:
        print_error(e)
        sys.exit(1)


@users.command()
@click.argument('domain_name', type=str, metavar='DOMAIN_NAME')
@click.argument('email', type=str, metavar='EMAIL')
@click.argument('password', type=str, metavar='PASSWORD')
@click.option('-u', '--username', type=str, default='', help='Username.')
@click.option('-n', '--full-name', type=str, default='', help='Full name.')
@click.option('-r', '--role', type=str, default='user',
              help='Role of the user. One of (admin, user, monitor).')
@click.option('-s', '--status', type=str, default='active',
              help='Account status. One of (active, inactive, deleted, before-verification).')
@click.option('--need-password-change', is_flag=True,
              help='Flag indicate that user needs to change password. '
                   'Useful when admin manually create password.')
@click.option('--description', type=str, default='', help='Description of the user.')
def add(domain_name, email, password, username, full_name, role, status,
        need_password_change, description):
    '''
    Add new user. A user must belong to a domain, so DOMAIN_NAME should be provided.

    \b
    DOMAIN_NAME: Name of the domain where new user belongs to.
    EMAIL: Email of new user.
    PASSWORD: Password of new user.
    '''
    with Session() as session:
        try:
            data = session.User.create(
                domain_name, email, password,
                username=username, full_name=full_name, role=role,
                status=status,
                need_password_change=need_password_change,
                description=description,
            )
        except Exception as e:
            print_error(e)
            sys.exit(1)
        if not data['ok']:
            print_fail('User creation has failed: {0}'.format(data['msg']))
            sys.exit(1)
        item = data['user']
        print('User {0} is created in domain {1}.'.format(item['email'], item['domain_name']))


@users.command()
@click.argument('email', type=str, metavar='EMAIL')
@click.option('-p', '--password', type=str, help='Password.')
@click.option('-u', '--username', type=str, help='Username.')
@click.option('-n', '--full-name', type=str, help='Full name.')
@click.option('-d', '--domain-name', type=str, help='Domain name.')
@click.option('-r', '--role', type=str, default='user',
              help='Role of the user. One of (admin, user, monitor).')
@click.option('-s', '--status', type=str,
              help='Account status. One of (active, inactive, deleted, before-verification).')
@click.option('--need-password-change', is_flag=True,
              help='Flag indicate that user needs to change password. '
                   'Useful when admin manually create password.')
@click.option('--description', type=str, default='', help='Description of the user.')
def update(email, password, username, full_name, domain_name, role, status,
           need_password_change, description):
    '''
    Update an existing user.

    EMAIL: Email of user to update.
    '''
    with Session() as session:
        try:
            data = session.User.update(
                email,
                password=password, username=username, full_name=full_name,
                domain_name=domain_name,
                role=role, status=status, need_password_change=need_password_change,
                description=description,
            )
        except Exception as e:
            print_error(e)
            sys.exit(1)
        if not data['ok']:
            print_fail('User update has failed: {0}'.format(data['msg']))
            sys.exit(1)
        print('User {0} is updated.'.format(email))


@users.command()
@click.argument('email', type=str, metavar='EMAIL')
def delete(email):
    """
    Inactivate an existing user.

    EMAIL: Email of user to inactivate.
    """
    with Session() as session:
        try:
            data = session.User.delete(email)
        except Exception as e:
            print_error(e)
            sys.exit(1)
        if not data['ok']:
            print_fail('User inactivation has failed: {0}'.format(data['msg']))
            sys.exit(1)
        print('User is inactivated: ' + email + '.')


@users.command()
@click.argument('email', type=str, metavar='EMAIL')
@click.option('--purge-shared-vfolders', is_flag=True, default=False,
              help='Delete user\'s all virtual folders. '
                   'If False, shared folders will not be deleted '
                   'and migrated the ownership to the requested admin.')
def purge(email, purge_shared_vfolders):
    """
    Delete an existing user. This action cannot be undone.

    NAME: Name of a domain to delete.
    """
    with Session() as session:
        try:
            if not ask_yn():
                print_info('Cancelled')
                sys.exit(1)
            data = session.User.purge(email, purge_shared_vfolders)
        except Exception as e:
            print_error(e)
            sys.exit(1)
        if not data['ok']:
            print_fail('User deletion has failed: {0}'.format(data['msg']))
            sys.exit(1)
        print('User is deleted: ' + email + '.')
