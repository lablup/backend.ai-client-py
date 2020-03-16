import sys
import click
from tabulate import tabulate

from . import admin
from ...session import Session
from ..pretty import print_done, print_warn, print_fail, print_error


@admin.command()
@click.option('--operation', is_flag=True, help='Get operational images only')
def images(operation):
    '''
    Show the list of registered images in this cluster.
    '''
    fields = [
        ('Name', 'name'),
        ('Registry', 'registry'),
        ('Tag', 'tag'),
        ('Digest', 'digest'),
        ('Size', 'size_bytes'),
        ('Aliases', 'aliases'),
    ]
    with Session() as session:
        try:
            items = session.Image.list(operation=operation,
                                       fields=(item[1] for item in fields))
        except Exception as e:
            print_error(e)
            sys.exit(1)
        if len(items) == 0:
            print_warn('There are no registered images.')
            return
        print(tabulate((item.values() for item in items),
                       headers=(item[0] for item in fields),
                       floatfmt=',.0f'))


@admin.command()
@click.option('-r', '--registry', type=str, default=None,
              help='The name (usually hostname or "lablup") '
                   'of the Docker registry configured.')
def rescan_images(registry):
    '''Update the kernel image metadata from all configured docker registries.'''
    with Session() as session:
        try:
            result = session.Image.rescan_images(registry)
        except Exception as e:
            print_error(e)
            sys.exit(1)
        if result['ok']:
            print_done("Updated the image metadata from the configured registries.")
        else:
            print_fail(f"Rescanning has failed: {result['msg']}")


@admin.command()
@click.argument('alias', type=str)
@click.argument('target', type=str)
def alias_image(alias, target):
    '''Add an image alias.'''
    with Session() as session:
        try:
            result = session.Image.alias_image(alias, target)
        except Exception as e:
            print_error(e)
            sys.exit(1)
        if result['ok']:
            print_done(f"An alias has created: {alias} -> {target}")
        else:
            print_fail(f"Aliasing has failed: {result['msg']}")


@admin.command()
@click.argument('alias', type=str)
def dealias_image(alias):
    '''Remove an image alias.'''
    with Session() as session:
        try:
            result = session.Image.dealias_image(alias)
        except Exception as e:
            print_error(e)
            sys.exit(1)
        if result['ok']:
            print_done(f"The alias has been removed: {alias}")
        else:
            print_fail(f"Dealiasing has failed: {result['msg']}")
