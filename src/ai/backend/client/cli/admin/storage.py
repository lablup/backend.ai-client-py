import json
import sys

import click
from tabulate import tabulate

from . import admin
from ...session import Session
from ..pretty import print_error
from ..pagination import (
    get_preferred_page_size,
    echo_via_pager,
    tabulate_items,
)
from ..utils import format_nested_dicts, format_value
from ...exceptions import NoItems


@admin.command()
@click.argument('vfolder_host')
def storage(vfolder_host):
    """
    Show the information about the given storage volume.
    (super-admin privilege required)
    """
    fields = [
        ('ID', 'id'),
        ('Backend', 'backend'),
        ('Capabilities', 'capabilities'),
        ('Path', 'path'),
        ('FS prefix', 'fsprefix'),
        ('Hardware Metadata', 'hardware_metadata'),
        ('Perf. Metric', 'performance_metric'),
    ]
    with Session() as session:
        try:
            resp = session.Storage.detail(
                vfolder_host=vfolder_host,
                fields=(item[1] for item in fields))
        except Exception as e:
            print_error(e)
            sys.exit(1)
        rows = []
        for name, key in fields:
            if key in resp:
                if key in ('hardware_metadata', 'performance_metric'):
                    rows.append((name, format_nested_dicts(json.loads(resp[key]))))
                else:
                    rows.append((name, format_value(resp[key])))
        print(tabulate(rows, headers=('Field', 'Value')))


@admin.command()
def storage_list():
    """
    List storage volumes.
    (super-admin privilege required)
    """
    fields = [
        ('ID', 'id'),
        ('Backend', 'backend'),
        ('Capabilities', 'capabilities'),
    ]
    try:
        with Session() as session:
            page_size = get_preferred_page_size()
            try:
                items = session.Storage.paginated_list(
                    fields=[f[1] for f in fields],
                    page_size=page_size,
                )
                echo_via_pager(
                    tabulate_items(items, fields)
                )
            except NoItems:
                print("There are no storage volumes.")
    except Exception as e:
        print_error(e)
        sys.exit(1)
