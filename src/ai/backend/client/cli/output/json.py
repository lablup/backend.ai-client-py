from __future__ import annotations

import json
from typing import (
    Callable,
    Sequence,
    Tuple,
)

from ...types import PaginatedResult
from . import BaseOutputHandler, T, _identity_func

_json_opts = {"indent": 2}


class JsonOutputHandler(BaseOutputHandler):

    def print_item(
        self,
        rows: Sequence[Tuple[str, T]],
        format_row: Callable[[T], T] = _identity_func,
    ) -> None:
        print(json.dumps(
            {
                "count": 1,
                "total_count": 1,
                "items": [
                    {k: format_row(v) for k, v in rows}
                ],
            },
            **_json_opts,
        ))

    def print_items(
        self,
        row_sets: Sequence[Sequence[Tuple[str, T]]],
        format_row: Callable[[T], T] = _identity_func,
    ) -> None:
        print(json.dumps(
            {
                "count": len(row_sets),
                "total_count": len(row_sets),
                "items": [
                    {k: format_row(v) for k, v in rows}
                    for rows in row_sets
                ],
            },
            **_json_opts,
        ))

    def print_paginated_list(
        self,
        fetch_func: Callable[[int, int], PaginatedResult[T]],
        initial_page_offset: int,
        page_size: int = None,
        format_item: Callable[[T], T] = _identity_func,
    ) -> None:
        page_size = page_size or 20
        result = fetch_func(initial_page_offset, page_size)
        print(json.dumps(
            {
                "count": len(result.items),
                "total_count": result.total_count,
                "items": [*map(format_item, result.items)],
            },
            **_json_opts,
        ))

    def print_error(
        self,
        error: Exception,
    ) -> None:
        print(json.dumps(
            {
                "error": str(error),
            },
            **_json_opts,
        ))
