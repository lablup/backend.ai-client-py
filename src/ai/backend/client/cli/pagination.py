import shutil
import sys
import textwrap
from typing import (
    cast,
    Any,
    Generator,
    Mapping,
    Sequence,
    Tuple,
)
from typing_extensions import (  # for Python 3.7
    TypedDict,
)

import click


class PaginatedResult(TypedDict):
    total_count: int
    items: Sequence[Any]


def execute_paginated_query(
    session,
    root_field: str,
    variables: Mapping[str, Tuple[Any, str]],
    fields: Sequence[str],
    *,
    limit: int,
    offset: int,
) -> PaginatedResult:
    query = '''
    query($limit:Int!, $offset:Int!, $var_decls) {
      $root_field(
          limit:$limit, offset:$offset, $var_args) {
        items { $fields }
        total_count
      }
    }'''
    query = query.replace('$root_field', root_field)
    query = query.replace('$fields', ' '.join(item[1] for item in fields))
    query = query.replace(
        '$var_decls',
        ', '.join(f'${key}: {value[1]}'
                  for key, value in variables.items()),
    )
    query = query.replace('$var_args', ', '.join(f'{key}:${key}' for key in variables.keys()))
    query = textwrap.dedent(query).strip()
    var_values = {key: value[0] for key, value in variables.items()}
    var_values['limit'] = limit
    var_values['offset'] = offset
    resp = session.Admin.query(query, var_values)
    return cast(PaginatedResult, resp[root_field])


def generate_paginated_results(
    session,
    root_field: str,
    variables: Mapping[str, Any],
    fields: Sequence[str],
    *,
    page_size: int,
) -> Generator[None, None, Any]:
    offset = 0
    is_first = True
    total_count = -1
    while True:
        limit = (page_size if is_first else
                 min(page_size, total_count - offset))
        result = execute_paginated_query(
            session, root_field, variables, fields,
            limit=limit, offset=offset,
        )
        offset += page_size
        total_count = result['total_count']
        items = result['items']
        yield from items
        is_first = False
        if offset >= total_count:
            break


def echo_via_pager(
    generator,
) -> None:
    """
    A variant of ``click.echo_via_pager()`` which implements our own simplified pagination.
    The key difference is that it holds the generator for each page, so that the generator
    won't continue querying the next results unless continued, avoiding server overloads.
    """
    # TODO: support PageUp & PageDn by buffering the output
    terminal_size = shutil.get_terminal_size((80, 20))
    line_count = 0
    for text in generator:
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
