from __future__ import annotations

from abc import ABCMeta, abstractmethod
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

from ..func.types import FieldSpec, PaginatedResult

if TYPE_CHECKING:
    from ai.backend.client.cli.types import CLIContext


class AbstractOutputFormatter(metaclass=ABCMeta):
    """
    The base implementation of output formats.
    """

    @abstractmethod
    def format_console(self, value: Any, field: CliFieldSpec) -> str:
        raise NotImplementedError

    @abstractmethod
    def format_json(self, value: Any, field: CliFieldSpec) -> Any:
        raise NotImplementedError


@attr.define(slots=True, frozen=True)
class CliFieldSpec(FieldSpec):
    """
    The specification on how to represent a GraphQL object field
    in the functional CLI output handlers.

    Attributes:
        formatter: The formatter instance which provide per-output-type format methods.
            (console and json)
    """

    formatter: AbstractOutputFormatter = attr.field()

    @formatter.default
    def _default_formatter(self) -> AbstractOutputFormatter:
        from .formatters import default_output_formatter  # avoid circular import
        return default_output_formatter


T = TypeVar('T')


@attr.define(slots=True)
class CliPaginatedResult(PaginatedResult, Generic[T]):
    fields: Sequence[CliFieldSpec]


class BaseOutputHandler(metaclass=ABCMeta):

    def __init__(self, cli_context: CLIContext) -> None:
        self.ctx = cli_context

    @abstractmethod
    def print_item(
        self,
        item: Mapping[str, Any] | None,
        fields: Sequence[CliFieldSpec],
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def print_items(
        self,
        items: Sequence[Mapping[str, Any]],
        fields: Sequence[CliFieldSpec],
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def print_list(
        self,
        items: Sequence[Mapping[str, Any]],
        fields: Sequence[CliFieldSpec],
        *,
        is_scalar: bool = False,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def print_paginated_list(
        self,
        fetch_func: Callable[[int, int], CliPaginatedResult[T]],
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
