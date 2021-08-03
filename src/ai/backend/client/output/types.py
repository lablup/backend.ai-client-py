from __future__ import annotations

from abc import ABCMeta, abstractmethod
from collections import UserDict
from typing import (
    Any,
    Callable,
    Generic,
    Mapping,
    Sequence,
    TypeVar,
    TYPE_CHECKING,
)

import attr

if TYPE_CHECKING:
    from ai.backend.client.cli.types import CLIContext


_predefined_humanized_field_names = {
    "id": "ID",
    "uuid": "UUID",
    "resource_policy": "Res.Policy",
    "concurrency_limit": "Concur.Limit",
    "concurrency_used": "Concur.Used",
    "fsprefix": "FS Prefix",
    "hardware_metadata": "HW Metadata",
    "performance_metric": "Perf.Metric",
}


def _make_camel_case(name: str) -> str:
    return " ".join(
        map(lambda s: s[0].upper() + s[1:], name.split("_"))
    )


class AbstractOutputFormatter(metaclass=ABCMeta):
    """
    The base implementation of output formats.
    """

    @abstractmethod
    def format_json(self, value):
        raise NotImplementedError

    @abstractmethod
    def format_console(self, value):
        raise NotImplementedError


@attr.define(slots=True, frozen=True)
class FieldSpec:
    field_ref: str = attr.field()
    humanized_name: str = attr.field()
    field_name: str = attr.field()
    alt_name: str = attr.field()
    formatter: AbstractOutputFormatter = attr.field()

    @humanized_name.default
    def _autogen_humanized_name(self) -> str:
        # to handle cases like "groups { id name }", "user_info { full_name }"
        field_name = self.field_ref.partition(" ")[0]
        if h := _predefined_humanized_field_names.get(field_name):
            return h
        if field_name.startswith("is_"):
            return _make_camel_case(field_name[3:]) + "?"
        return _make_camel_case(field_name)

    @field_name.default
    def _default_field_name(self) -> str:
        return self.field_ref.partition(" ")[0]

    @alt_name.default
    def _default_alt_name(self) -> str:
        return self.field_ref.partition(" ")[0]

    @formatter.default
    def _default_formatter(self) -> AbstractOutputFormatter:
        from .formatters import default_output_formatter  # avoid circular import
        return default_output_formatter


class FieldSet(UserDict):

    def __init__(self, fields: Sequence[FieldSpec]) -> None:
        self.data = {
            f.alt_name: f for f in fields
        }


T = TypeVar('T')


@attr.define(slots=True)
class PaginatedResult(Generic[T]):
    total_count: int
    items: Sequence[T]
    fields: Sequence[FieldSpec]


class BaseOutputHandler(metaclass=ABCMeta):

    def __init__(self, cli_context: CLIContext) -> None:
        self.ctx = cli_context

    @abstractmethod
    def print_item(
        self,
        item: Mapping[str, Any] | None,
        fields: Sequence[FieldSpec],
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def print_items(
        self,
        items: Sequence[Mapping[str, Any]],
        fields: Sequence[FieldSpec],
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def print_paginated_list(
        self,
        fetch_func: Callable[[int, int], PaginatedResult[T]],
        initial_page_offset: int,
        page_size: int = None,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def print_error(
        self,
        error: Exception,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def print_fail(
        self,
        message: str,
    ) -> None:
        raise NotImplementedError
