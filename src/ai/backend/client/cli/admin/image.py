import json
import sys

import click
from tabulate import tabulate
from tqdm import tqdm

from . import admin
from ...compat import asyncio_run
from ...session import Session, AsyncSession
from ..pretty import print_done, print_warn, print_fail, print_error


@admin.command()
@click.option('--operation', is_flag=True, help='Get operational images only')
def images(operation: bool) -> None:
    """
    Show the list of registered images in this cluster.
    """
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
                       headers=[item[0] for item in fields],
                       floatfmt=',.0f'))


@admin.command()
@click.option('-r', '--registry', type=str, default=None,
              help='The name (usually hostname or "lablup") '
                   'of the Docker registry configured.')
def rescan_images(registry: str) -> None:
    """
    Update the kernel image metadata from all configured docker registries.
    """

    async def rescan_images_impl(registry: str) -> None:
        async with AsyncSession() as session:
            try:
                result = await session.Image.rescan_images(registry)
            except Exception as e:
                print_error(e)
                sys.exit(1)
            if not result['ok']:
                print_fail(f"Failed to begin registry scanning: {result['msg']}")
                sys.exit(1)
            print_done("Started updating the image metadata from the configured registries.")
            task_id = result['task_id']
            bgtask = session.BackgroundTask(task_id)
            try:
                completion_msg_func = lambda: print_done("Finished registry scanning.")
                with tqdm(unit='image') as pbar:
                    async with bgtask.listen_events() as response:
                        async for ev in response:
                            data = json.loads(ev.data)
                            if ev.event == 'task_updated':
                                pbar.total = data['total_progress']
                                pbar.write(data['message'])
                                pbar.update(data['current_progress'] - pbar.n)
                            elif ev.event == 'task_failed':
                                error_msg = data['message']
                                completion_msg_func = \
                                    lambda: print_fail(f"Error occurred: {error_msg}")
                            elif ev.event == 'task_cancelled':
                                completion_msg_func = \
                                    lambda: print_warn("Registry scanning has been "
                                                       "cancelled in the middle.")
            finally:
                completion_msg_func()

    asyncio_run(rescan_images_impl(registry))


@admin.command()
@click.argument('alias', type=str)
@click.argument('target', type=str)
def alias_image(alias, target):
    """Add an image alias."""
    with Session() as session:
        try:
            result = session.Image.alias_image(alias, target)
        except Exception as e:
            print_error(e)
            sys.exit(1)
        if result['ok']:
            print_done(f"An alias has created: {alias} -> {target}")
        else:
            print_fail("Aliasing has failed: {0}".format(result['msg']))


@admin.command()
@click.argument('alias', type=str)
def dealias_image(alias):
    """Remove an image alias."""
    with Session() as session:
        try:
            result = session.Image.dealias_image(alias)
        except Exception as e:
            print_error(e)
            sys.exit(1)
        if result['ok']:
            print_done(f"The alias has been removed: {alias}")
        else:
            print_fail("Dealiasing has failed: {0}".format(result['msg']))
