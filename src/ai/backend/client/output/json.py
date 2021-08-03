from __future__ import annotations

import json
from typing import (
    Any,
    Callable,
    Mapping,
    Sequence,
    TypeVar,
)

from .types import BaseOutputHandler, PaginatedResult, FieldSpec

_json_opts: Mapping[str, Any] = {"indent": 2}

T = TypeVar('T')


class JsonOutputHandler(BaseOutputHandler):

    def print_item(
        self,
        item: Mapping[str, Any] | None,
        fields: Sequence[FieldSpec],
    ) -> None:
        if item is None:
            print(json.dumps({
                "count": 0,
                "total_count": 0,
                "items": [],
            }))
            return
        field_map = {f.field_name: f for f in fields}
        print(json.dumps(
            {
                "count": 1,
                "total_count": 1,
                "items": [
                    {
                        field_map[k].alt_name: field_map[k].formatter.format_json(v, field_map[k])
                        for k, v in item.items()
                    }
                ],
            },
            **_json_opts,
        ))

    def print_items(
        self,
        items: Sequence[Mapping[str, Any]],
        fields: Sequence[FieldSpec],
    ) -> None:
        field_map = {f.field_name: f for f in fields}
        print(json.dumps(
            {
                "count": len(items),
                "total_count": len(items),
                "items": [
                    {
                        field_map[k].alt_name: field_map[k].formatter.format_json(v, field_map[k])
                        for k, v in item.items()
                    } for item in items
                ],
            },
            **_json_opts,
        ))

    def print_paginated_list(
        self,
        fetch_func: Callable[[int, int], PaginatedResult],
        initial_page_offset: int,
        page_size: int = None,
    ) -> None:
        page_size = page_size or 20
        result = fetch_func(initial_page_offset, page_size)
        field_map = {f.field_name: f for f in result.fields}
        print(json.dumps(
            {
                "count": len(result.items),
                "total_count": result.total_count,
                "items": [
                    {
                        field_map[k].alt_name: field_map[k].formatter.format_json(v, field_map[k])
                        for k, v in item.items()
                    }
                    for item in result.items
                ]
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

    def print_fail(
        self,
        message: str,
    ) -> None:
        print(json.dumps(
            {
                "error": message,
            },
            **_json_opts,
        ))
