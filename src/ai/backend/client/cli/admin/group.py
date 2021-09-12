import sys
import uuid

import click

from ai.backend.client.session import Session
from ai.backend.client.func.group import (
    _default_list_fields,
    _default_detail_fields,
)
# from ai.backend.client.output.fields import group_fields
from . import admin
from ..interaction import ask_yn
from ..pretty import print_error, print_info, print_fail

from ..types import CLIContext


@admin.group()
def group() -> None:
    """
    User group (project) administration commands
    """


@group.command()
@click.pass_obj
@click.argument('id_or_name', type=str)
def info(ctx: CLIContext, id_or_name: str) -> None:
    """
    Show the information about the group(s) having the given name.
    Two or more groups in different domains may have the same name,
    so this may print out information of multiple groups if queried
    by a superadmin.

    When queried with a human-readable name by a super-admin,
    it may return multiple results with the same name from
    different domains.

    \b
    id_or_name: Group ID (UUID) or name.
    """
    with Session() as session:
        try:
            gid = uuid.UUID(id_or_name)
        except ValueError:
            # interpret as name
            try:
                item = session.Group.from_name(id_or_name)
                ctx.output.print_item(item, _default_detail_fields)
            except Exception as e:
                ctx.output.print_error(e)
                sys.exit(1)
        else:
            # interpret as UUID
            try:
                item = session.Group.detail(gid=str(gid))
                ctx.output.print_item(item, _default_detail_fields)
            except Exception as e:
                ctx.output.print_error(e)
                sys.exit(1)


@group.command()
@click.pass_obj
@click.option('-d', '--domain-name', type=str, default=None,
              help='Domain name to list groups belongs to it.')
def list(ctx: CLIContext, domain_name) -> None:
    """
    List groups in the given domain.
    (admin privilege required)
    """
    with Session() as session:
        try:
            items = session.Group.list(domain_name=domain_name)
            ctx.output.print_list(items, _default_list_fields)
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(1)


@group.command()
@click.argument('domain_name', type=str, metavar='DOMAIN_NAME')
@click.argument('name', type=str, metavar='NAME')
@click.option('-d', '--description', type=str, default='',
              help='Description of new group.')
@click.option('-i', '--inactive', is_flag=True,
              help='New group will be inactive.')
@click.option('--total-resource-slots', type=str, default='{}',
              help='Set total resource slots.')
@click.option('--allowed-vfolder-hosts', type=str, multiple=True,
              help='Allowed virtual folder hosts.')
def add(domain_name, name, description, inactive, total_resource_slots,
        allowed_vfolder_hosts):
    """
    Add new group. A group must belong to a domain, so DOMAIN_NAME should be provided.

    \b
    DOMAIN_NAME: Name of the domain where new group belongs to.
    NAME: Name of new group.
    """
    with Session() as session:
        try:
            data = session.Group.create(
                domain_name, name,
                description=description,
                is_active=not inactive,
                total_resource_slots=total_resource_slots,
                allowed_vfolder_hosts=allowed_vfolder_hosts,
            )
        except Exception as e:
            print_error(e)
            sys.exit(1)
        if not data['ok']:
            print_fail('Group creation has failed: {0}'.format(data['msg']))
            sys.exit(1)
        item = data['group']
        print('Group name {0} is created in domain {1}.'.format(item['name'], item['domain_name']))


@group.command()
@click.argument('gid', type=str, metavar='GROUP_ID')
@click.option('-n', '--name', type=str, help='New name of the group')
@click.option('-d', '--description', type=str, help='Description of the group')
@click.option('--is-active', type=bool, help='Set group inactive.')
@click.option('--total-resource-slots', type=str, help='Update total resource slots.')
@click.option('--allowed-vfolder-hosts', type=str, multiple=True,
              help='Allowed virtual folder hosts.')
def update(gid, name, description, is_active, total_resource_slots,
           allowed_vfolder_hosts):
    """
    Update an existing group. Domain name is not necessary since group ID is unique.

    GROUP_ID: Group ID to update.
    """
    with Session() as session:
        try:
            data = session.Group.update(
                gid,
                name=name,
                description=description,
                is_active=is_active,
                total_resource_slots=total_resource_slots,
                allowed_vfolder_hosts=allowed_vfolder_hosts,
            )
        except Exception as e:
            print_error(e)
            sys.exit(1)
        if not data['ok']:
            print_fail('Group update has failed: {0}'.format(data['msg']))
            sys.exit(1)
        print('Group {0} is updated.'.format(gid))


@group.command()
@click.argument('gid', type=str, metavar='GROUP_ID')
def delete(gid):
    """
    Inactivates the existing group. Does not actually delete it for safety.

    GROUP_ID: Group ID to inactivate.
    """
    with Session() as session:
        try:
            data = session.Group.delete(gid)
        except Exception as e:
            print_error(e)
            sys.exit(1)
        if not data['ok']:
            print_fail('Group inactivation has failed: {0}'.format(data['msg']))
            sys.exit(1)
        print('Group is inactivated: ' + gid + '.')


@group.command()
@click.argument('gid', type=str, metavar='GROUP_ID')
def purge(gid):
    """
    Delete the existing group. This action cannot be undone.

    GROUP_ID: Group ID to inactivate.
    """
    with Session() as session:
        try:
            if not ask_yn():
                print_info('Cancelled')
                sys.exit(1)
            data = session.Group.purge(gid)
        except Exception as e:
            print_error(e)
            sys.exit(1)
        if not data['ok']:
            print_fail('Group deletion has failed: {0}'.format(data['msg']))
            sys.exit(1)
        print('Group is deleted: ' + gid + '.')


@group.command()
@click.argument('gid', type=str, metavar='GROUP_ID')
@click.argument('user_uuids', type=str, metavar='USER_UUIDS', nargs=-1)
def add_users(gid, user_uuids):
    """
    Add users to a group.

    \b
    GROUP_ID: Group ID where users will be belong to.
    USER_UUIDS: List of users' uuids to be added to the group.
    """
    with Session() as session:
        try:
            data = session.Group.add_users(gid, user_uuids)
        except Exception as e:
            print_error(e)
            sys.exit(1)
        if not data['ok']:
            print_fail('Error on adding users to group: {0}'.format(data['msg']))
            sys.exit(1)
        print('Users are added to the group')


@group.command()
@click.argument('gid', type=str, metavar='GROUP_ID')
@click.argument('user_uuids', type=str, metavar='USER_UUIDS', nargs=-1)
def remove_users(gid, user_uuids):
    """
    Remove users from a group.

    \b
    GROUP_ID: Group ID where users currently belong to.
    USER_UUIDS: List of users' uuids to be removed from the group.
    """
    with Session() as session:
        try:
            data = session.Group.remove_users(gid, user_uuids)
        except Exception as e:
            print_error(e)
            sys.exit(1)
        if not data['ok']:
            print_fail('Error on removing users to group: {0}'.format(data['msg']))
            sys.exit(1)
        print('Users are removed from the group')
