import sys
from tabulate import tabulate

from . import admin
from ...session import Session
from ..pretty import print_error


@admin.command()
def images():
    '''
    Show the list of registered images in this cluster.
    '''
    fields = [
        ('Name', 'name'),
        ('Registry', 'registry'),
        ('Tag', 'tag'),
        ('Digest', 'digest'),
    ]
    with Session() as session:
        try:
            items = session.Image.list(fields=(item[1] for item in fields))
        except Exception as e:
            print_error(e)
            sys.exit(1)
        if len(items) == 0:
            print('There are no registered images.')
            return
        print(tabulate((item.values() for item in items),
                       headers=(item[0] for item in fields)))
