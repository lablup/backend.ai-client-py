import shutil
import sys
from typing import (
    Iterable,
)

import click
from tabulate import tabulate

from ..pagination import MAX_PAGE_SIZE


def get_preferred_page_size() -> int:
    return min(MAX_PAGE_SIZE, shutil.get_terminal_size((80, 20)).lines)


def tabulate_items(
    items, page_size, fields,
    *,
    item_formatter,
    tablefmt: str = 'simple',
):
    is_first = True
    output_count = 0
    buffered_items = []
    # If we iterate until the end of items, pausing the terminal output
    # would not have effects for avoiding unnecessary queries for subsequent pages.
    # Let's buffer the items and split the formatting per page.
    for item in items:
        buffered_items.append(item)
        output_count += 1
        item_formatter(item)
        if output_count == page_size:
            table = tabulate(
                [item.values() for item in buffered_items],
                headers=(
                    [] if tablefmt == 'plain'
                    else [item[0] for item in fields]
                ),
                tablefmt=tablefmt,
            )
            table_rows = table.splitlines()
            if is_first:
                yield from (row + '\n' for row in table_rows)
            else:
                # strip the header for continued page outputs
                yield from (row + '\n' for row in table_rows[2:])
            buffered_items.clear()
            is_first = False
            output_count = 0


def echo_via_pager(
    text_generator: Iterable[str],
) -> None:
    """
    A variant of ``click.echo_via_pager()`` which implements our own simplified pagination.
    The key difference is that it holds the generator for each page, so that the generator
    won't continue querying the next results unless continued, avoiding server overloads.
    """
    # TODO: support PageUp & PageDn by buffering the output
    terminal_size = shutil.get_terminal_size((80, 20))
    line_count = 0
    for text in text_generator:
        line_count += text.count('\n')
        click.echo(text, nl=False)
        if line_count == terminal_size.lines - 1:
            if sys.stdin.isatty() and sys.stdout.isatty():
                click.echo(':', nl=False)
                # Pause the terminal so that we don't execute next-page queries indefinitely.
                # Since click.pause() ignores KeyboardInterrupt, we just use click.getchar()
                # to allow user interruption.
                k = click.getchar(echo=False)
                if k in ('q', 'Q'):
                    break
                click.echo('\r', nl=False)
            line_count = 0
