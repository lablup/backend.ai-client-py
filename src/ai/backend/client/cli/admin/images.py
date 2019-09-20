import sys
import click
from tabulate import tabulate

from . import admin
from ...session import Session
from ..pretty import print_error


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
            print('There are no registered images.')
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
            result = session.Image.rescanImages(registry)
        except Exception as e:
            print_error(e)
            sys.exit(1)
        if result['ok']:
            print("kernel image metadata updated")
        else:
            print("rescanning failed: {0}".format(result['msg']))


@admin.command()
@click.argument('alias', type=str)
@click.argument('target', type=str)
def alias_image(alias, target):
    '''Add an image alias.'''
    with Session() as session:
        try:
            result = session.Image.aliasImage(alias, target)
        except Exception as e:
            print_error(e)
            sys.exit(1)
        if result['ok']:
            print("alias {0} created for target {1}".format(alias, target))
        else:
            print(result['msg'])


@admin.command()
@click.argument('alias', type=str)
def dealias_image(alias):
    '''Remove an image alias.'''
    with Session() as session:
        try:
            result = session.Image.dealiasImage(alias)
        except Exception as e:
            print_error(e)
            sys.exit(1)
        if result['ok']:
            print("alias {0} removed.".format(alias))
        else:
            print(result['msg'])
