import textwrap
from typing import (
    cast,
    Any,
    AsyncIterator,
    Dict,
    Sequence,
    Tuple,
)
from typing_extensions import (  # for Python 3.7
    Final,
    TypedDict,
)

from .exceptions import NoItems, BackendAPIVersionError
from .session import api_session

MAX_PAGE_SIZE: Final = 100


class PaginatedResult(TypedDict):
    total_count: int
    items: Sequence[Any]


async def execute_paginated_query(
    root_field: str,
    variables: Dict[str, Tuple[Any, str]],
    fields: Sequence[str],
    *,
    limit: int,
    offset: int,
) -> PaginatedResult:
    if limit > MAX_PAGE_SIZE:
        raise ValueError(f"The page size cannot exceed {MAX_PAGE_SIZE}")
    query = '''
    query($limit:Int!, $offset:Int!, $var_decls) {
      $root_field(
          limit:$limit, offset:$offset, $var_args) {
        items { $fields }
        total_count
      }
    }'''
    query = query.replace('$root_field', root_field)
    query = query.replace('$fields', ' '.join(fields))
    query = query.replace(
        '$var_decls',
        ', '.join(f'${key}: {value[1]}'
                  for key, value in variables.items()),
    )
    query = query.replace(
        '$var_args',
        ', '.join(f'{key}:${key}'
                  for key in variables.keys())
    )
    query = textwrap.dedent(query).strip()
    var_values = {key: value[0] for key, value in variables.items()}
    var_values['limit'] = limit
    var_values['offset'] = offset
    data = await api_session.get().Admin._query(query, var_values)
    return cast(PaginatedResult, data[root_field])


async def generate_paginated_results(
    root_field: str,
    variables: Dict[str, Tuple[Any, str]],
    fields: Sequence[str],
    *,
    page_size: int,
) -> AsyncIterator[Any]:
    if page_size > MAX_PAGE_SIZE:
        raise ValueError(f"The page size cannot exceed {MAX_PAGE_SIZE}")
    if api_session.get().api_version < (6, '20210815'):
        if variables['filter'][0] is not None or variables['order'][0] is not None:
            raise BackendAPIVersionError(
                "filter and order arguments for paginated lists require v6.20210815 or later."
            )
        # should remove to work with older managers
        variables.pop('filter')
        variables.pop('order')
    offset = 0
    total_count = -1
    while True:
        limit = page_size
        result = await execute_paginated_query(
            root_field, variables, fields,
            limit=limit, offset=offset,
        )
        offset += page_size
        total_count = result['total_count']
        if total_count == 0:
            raise NoItems
        for item in result['items']:
            yield item
        if offset >= total_count:
            break
