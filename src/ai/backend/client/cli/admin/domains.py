import sys

import click
from tabulate import tabulate

from . import admin
from ..interaction import ask_yn
from ..pretty import print_error, print_info, print_fail
from ...session import Session


@admin.command()
@click.option('-n', '--name', type=str, default=None,
              help="Domain name to get information.")
def domain(name):
    '''
    Show the information about the given domain.
    If name is not give, user's own domain information will be retrieved.
    '''
    fields = [
        ('Name', 'name'),
        ('Description', 'description'),
        ('Active?', 'is_active'),
        ('Created At', 'created_at'),
        ('Total Resource Slots', 'total_resource_slots'),
        ('Allowed vFolder Hosts', 'allowed_vfolder_hosts'),
        ('Allowed Docker Registries', 'allowed_docker_registries'),
        ('Scaling Groups', 'scaling_groups'),
    ]
    with Session() as session:
        try:
            resp = session.Domain.detail(name=name,
                                         fields=(item[1] for item in fields))
        except Exception as e:
            print_error(e)
            sys.exit(1)
        rows = []
        for name, key in fields:
            if key in resp:
                rows.append((name, resp[key]))
        print(tabulate(rows, headers=('Field', 'Value')))


@admin.group(invoke_without_command=True)
@click.pass_context
def domains(ctx):
    '''
    List and manage domains.
    (admin privilege required)
    '''
    if ctx.invoked_subcommand is not None:
        return
    fields = [
        ('Name', 'name'),
        ('Description', 'description'),
        ('Active?', 'is_active'),
        ('Created At', 'created_at'),
        ('Total Resource Slots', 'total_resource_slots'),
        ('Allowed vFolder Hosts', 'allowed_vfolder_hosts'),
        ('Allowed Docker Registries', 'allowed_docker_registries'),
        ('Scaling Groups', 'scaling_groups'),
    ]
    with Session() as session:
        try:
            resp = session.Domain.list(fields=(item[1] for item in fields))
        except Exception as e:
            print_error(e)
            sys.exit(1)
        if len(resp) < 1:
            print('There is no domain.')
            return
        fields = [field for field in fields if field[1] in resp[0]]
        print(tabulate((item.values() for item in resp),
                        headers=(item[0] for item in fields)))


@domains.command()
@click.argument('name', type=str, metavar='NAME')
@click.option('-d', '--description', type=str, default='',
              help='Description of new domain')
@click.option('-i', '--inactive', is_flag=True,
              help='New domain will be inactive.')
@click.option('--total-resource-slots', type=str, default='{}',
              help='Set total resource slots.')
@click.option('--allowed-vfolder-hosts', type=str, multiple=True,
              help='Allowed virtual folder hosts.')
@click.option('--allowed-docker-registries', type=str, multiple=True,
              help='Allowed docker registries.')
def add(name, description, inactive, total_resource_slots,
        allowed_vfolder_hosts, allowed_docker_registries):
    '''
    Add a new domain.

    NAME: Name of new domain.
    '''
    with Session() as session:
        try:
            data = session.Domain.create(
                name,
                description=description,
                is_active=not inactive,
                total_resource_slots=total_resource_slots,
                allowed_vfolder_hosts=allowed_vfolder_hosts,
                allowed_docker_registries=allowed_docker_registries,
            )
        except Exception as e:
            print_error(e)
            sys.exit(1)
        if not data['ok']:
            print_fail('Domain creation has failed: {0}'.format(data['msg']))
            sys.exit(1)
        item = data['domain']
        print('Domain name {0} is created.'.format(item['name']))


@domains.command()
@click.argument('name', type=str, metavar='NAME')
@click.option('--new-name', type=str, help='New name of the domain')
@click.option('--description', type=str, help='Description of the domain')
@click.option('--is-active', type=bool, help='Set domain inactive.')
@click.option('--total-resource-slots', type=str,
              help='Update total resource slots.')
@click.option('--allowed-vfolder-hosts', type=str, multiple=True,
              help='Allowed virtual folder hosts.')
@click.option('--allowed-docker-registries', type=str, multiple=True,
              help='Allowed docker registries.')
def update(name, new_name, description, is_active, total_resource_slots,
           allowed_vfolder_hosts, allowed_docker_registries):
    '''
    Update an existing domain.

    NAME: Name of new domain.
    '''
    with Session() as session:
        try:
            data = session.Domain.update(
                name,
                new_name=new_name,
                description=description,
                is_active=is_active,
                total_resource_slots=total_resource_slots,
                allowed_vfolder_hosts=allowed_vfolder_hosts,
                allowed_docker_registries=allowed_docker_registries,
            )
        except Exception as e:
            print_error(e)
            sys.exit(1)
        if not data['ok']:
            print_fail('Domain update has failed: {0}'.format(data['msg']))
            sys.exit(1)
        print('Domain {0} is updated.'.format(name))


@domains.command()
@click.argument('name', type=str, metavar='NAME')
def delete(name):
    """
    Inactive an existing domain.

    NAME: Name of a domain to inactive.
    """
    with Session() as session:
        try:
            data = session.Domain.delete(name)
        except Exception as e:
            print_error(e)
            sys.exit(1)
        if not data['ok']:
            print_fail('Domain inactivation has failed: {0}'.format(data['msg']))
            sys.exit(1)
        print('Domain is inactivated: ' + name + '.')


@domains.command()
@click.argument('name', type=str, metavar='NAME')
def purge(name):
    """
    Delete an existing domain.

    NAME: Name of a domain to delete.
    """
    with Session() as session:
        try:
            if not ask_yn():
                print_info('Cancelled')
                sys.exit(1)
            data = session.Domain.purge(name)
        except Exception as e:
            print_error(e)
            sys.exit(1)
        if not data['ok']:
            print_fail('Domain deletion has failed: {0}'.format(data['msg']))
            sys.exit(1)
        print('Domain is deleted: ' + name + '.')
