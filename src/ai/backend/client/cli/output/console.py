from __future__ import annotations

import sys
from typing import (
    Any,
    Callable,
    Mapping,
    Sequence,
    Tuple,
    TypeVar,
)

from tabulate import tabulate

from ...types import FieldSpec, PaginatedResult
from ..pretty import print_error as pretty_error, print_fail
from ..pagination import echo_via_pager, get_preferred_page_size, tabulate_items
from . import BaseOutputHandler, _identity_func


T = TypeVar('T')


class NoItems(Exception):
    pass


class ConsoleOutputHandler(BaseOutputHandler):

    def print_item(
        self,
        item: Mapping[str, Any] | None,
        fields: Sequence[FieldSpec],
    ) -> None:
        if item is None:
            print_fail("No matching entry found.")
        field_map = {f.field_name.partition(" ")[0]: f for f in fields}
        print(tabulate(
            [
                (field_map[k].humanized_name, field_map[k].format(v))
                for k, v in item.items()
            ],
            headers=('Field', 'Value'),
        ))

    def print_items(
        self,
        items: Sequence[Mapping[str, Any]],
        fields: Sequence[FieldSpec],
    ) -> None:
        field_map = {f.field_name.partition(" ")[0]: f for f in fields}
        for idx, item in enumerate(items):
            if idx > 0:
                print("-" * 20)
            print(tabulate(
                [
                    (field_map[k].humanized_name, field_map[k].format(v))
                    for k, v in item.items()
                ],
                headers=('Field', 'Value'),
            ))

    def print_paginated_list(
        self,
        fetch_func: Callable[[int, int], PaginatedResult[T]],
        initial_page_offset: int,
        page_size: int = None,
    ) -> None:
        if sys.stdout.isatty():
            page_size = page_size or get_preferred_page_size()

            def infinite_fetch():
                current_offset = initial_page_offset
                while True:
                    result = fetch_func(current_offset, page_size)
                    if result.total_count == 0:
                        raise NoItems
                    current_offset += result
                    yield from result.items
                    if current_offset >= result.total_count:
                        break

            try:
                echo_via_pager(
                    tabulate_items(
                        map(format_item, infinite_fetch()),
                        result.fields,
                    )
                )
            except NoItems:
                print("No matching items.")
        else:
            page_size = page_size or 20
            result = fetch_func(initial_page_offset, page_size)
            field_map = {f.field_name: f for f in result.fields}
            print(
                tabulate_items(
                    map(format_item, result.items),
                    result.fields,
                )
            )

    def print_error(
        self,
        error: Exception,
    ) -> None:
        pretty_error(error)
