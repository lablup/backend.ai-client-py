import sys

import click
from tabulate import tabulate

from . import admin
from ..pretty import print_done, print_warn, print_error, print_fail
from ...session import Session


@admin.command()
@click.argument('group', type=str, metavar='GROUP_NAME')
def list_scaling_groups(group):
    with Session() as session:
        try:
            resp = session.ScalingGroup.list_available(group)
        except Exception as e:
            print_error(e)
            sys.exit(1)
        if len(resp) < 1:
            print_warn('There is no scaling group available.')
            return
        print(resp)


@admin.command()
@click.option('-n', '--name', type=str, default=None,
              help="Name of a scaling group.")
def scaling_group(name):
    '''
    Show the information about the given scaling group.
    (superadmin privilege required)
    '''
    fields = [
        ('Name', 'name'),
        ('Description', 'description'),
        ('Active?', 'is_active'),
        ('Created At', 'created_at'),
        ('Driver', 'driver'),
        ('Driver Opts', 'driver_opts'),
        ('Scheduler', 'scheduler'),
        ('Scheduler Opts', 'scheduler_opts'),
    ]
    with Session() as session:
        try:
            resp = session.ScalingGroup.detail(
                name=name, fields=(item[1] for item in fields))
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
def scaling_groups(ctx):
    '''
    List and manage scaling groups.
    (superadmin privilege required)
    '''
    if ctx.invoked_subcommand is not None:
        return
    fields = [
        ('Name', 'name'),
        ('Description', 'description'),
        ('Active?', 'is_active'),
        ('Created At', 'created_at'),
        ('Driver', 'driver'),
        ('Driver Opts', 'driver_opts'),
        ('Scheduler', 'scheduler'),
        ('Scheduler Opts', 'scheduler_opts'),
    ]
    with Session() as session:
        try:
            resp = session.ScalingGroup.list(fields=(item[1] for item in fields))
        except Exception as e:
            print_error(e)
            sys.exit(1)
        if len(resp) < 1:
            print('There is no scaling group.')
            return
        fields = [field for field in fields if field[1] in resp[0]]
        print(tabulate((item.values() for item in resp),
                        headers=(item[0] for item in fields)))


@scaling_groups.command()
@click.argument('name', type=str, metavar='NAME')
@click.option('-d', '--description', type=str, default='',
              help='Description of new scaling group')
@click.option('-i', '--inactive', is_flag=True,
              help='New scaling group will be inactive.')
@click.option('--driver', type=str, default='static',
              help='Set driver.')
@click.option('--driver_opts', type=str, default={},
              help='Set driver options.')
@click.option('--scheduler', type=str, default='fifo',
              help='Set scheduler.')
@click.option('--scheduler_opts', type=str, default={},
              help='Set scheduler options.')
def add(name, description, inactive,
        driver, driver_opts, scheduler, scheduler_opts):
    '''
    Add a new scaling group.

    NAME: Name of new scaling group.
    '''
    with Session() as session:
        try:
            data = session.ScalingGroup.create(
                name,
                description=description,
                is_active=not inactive,
                driver=driver,
                driver_opts=driver_opts,
                scheduler=scheduler,
                scheduler_opts=scheduler_opts,
            )
        except Exception as e:
            print_error(e)
            sys.exit(1)
        if not data['ok']:
            print_fail('Scaling group creation has failed: {0}'.format(data['msg']))
            sys.exit(1)
        item = data['scaling_group']
        print_done('Scaling group name {0} is created.'.format(item['name']))


@scaling_groups.command()
@click.argument('name', type=str, metavar='NAME')
@click.option('-d', '--description', type=str, default='',
              help='Description of new scaling group')
@click.option('-i', '--inactive', is_flag=True,
              help='New scaling group will be inactive.')
@click.option('--driver', type=str, default='static',
              help='Set driver.')
@click.option('--driver_opts', type=str, default={},
              help='Set driver options.')
@click.option('--scheduler', type=str, default='fifo',
              help='Set scheduler.')
@click.option('--scheduler_opts', type=str, default={},
              help='Set scheduler options.')
def update(name, description, inactive,
           driver, driver_opts, scheduler, scheduler_opts):
    '''
    Update existing scaling group.

    NAME: Name of new scaling group.
    '''
    with Session() as session:
        try:
            data = session.ScalingGroup.update(
                name,
                description=description,
                is_active=not inactive,
                driver=driver,
                driver_opts=driver_opts,
                scheduler=scheduler,
                scheduler_opts=scheduler_opts,
            )
        except Exception as e:
            print_error(e)
            sys.exit(1)
        if not data['ok']:
            print_fail('Scaling group update has failed: {0}'.format(data['msg']))
            sys.exit(1)
        print_done('Scaling group {0} is updated.'.format(name))


@scaling_groups.command()
@click.argument('name', type=str, metavar='NAME')
def delete(name):
    """
    Delete an existing scaling group.

    NAME: Name of a scaling group to delete.
    """
    with Session() as session:
        try:
            data = session.ScalingGroup.delete(name)
        except Exception as e:
            print_error(e)
            sys.exit(1)
        if not data['ok']:
            print_fail('Scaling group deletion has failed: {0}'.format(data['msg']))
            sys.exit(1)
        print_done('Scaling group is deleted: ' + name + '.')


@scaling_groups.command()
@click.argument('scaling_group', type=str, metavar='SCALING_GROUP')
@click.argument('domain', type=str, metavar='DOMAIN')
def associate_scaling_group(scaling_group, domain):
    """
    Associate a domain with a scaling_group.

    \b
    SCALING_GROUP: The name of a scaling group.
    DOMAIN: The name of a domain.
    """
    with Session() as session:
        try:
            data = session.ScalingGroup.associate_domain(scaling_group, domain)
        except Exception as e:
            print_error(e)
            sys.exit(1)
        if not data['ok']:
            print_fail('Associating scaling group with domain failed: {0}'.format(data['msg']))
            sys.exit(1)
        print_done('Scaling group {} is assocatiated with domain {}.'.format(scaling_group, domain))


@scaling_groups.command()
@click.argument('scaling_group', type=str, metavar='SCALING_GROUP')
@click.argument('domain', type=str, metavar='DOMAIN')
def dissociate_scaling_group(scaling_group, domain):
    """
    Dissociate a domain from a scaling_group.

    \b
    SCALING_GROUP: The name of a scaling group.
    DOMAIN: The name of a domain.
    """
    with Session() as session:
        try:
            data = session.ScalingGroup.dissociate_domain(scaling_group, domain)
        except Exception as e:
            print_error(e)
            sys.exit(1)
        if not data['ok']:
            print_fail('Dissociating scaling group from domain failed: {0}'.format(data['msg']))
            sys.exit(1)
        print_done('Scaling group {} is dissociated from domain {}.'.format(scaling_group, domain))
