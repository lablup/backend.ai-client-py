from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import (
    Callable,
    Sequence,
    Tuple,
    TypeVar,
)

from ...pagination import PaginatedResult
from ..types import CLIContext, OutputMode

_identity_func = lambda item: item

T = TypeVar('T', bound=dict)


def get_output_handler(cli_ctx: CLIContext, output_mode: OutputMode) -> BaseOutputHandler:
    if output_mode == OutputMode.JSON:
        from .json import JsonOutputHandler
        return JsonOutputHandler(cli_ctx)
    elif output_mode == OutputMode.CONSOLE:
        from .console import ConsoleOutputHandler
        return ConsoleOutputHandler(cli_ctx)
    raise RuntimeError("Invalid output handler", output_mode)


class BaseOutputHandler(metaclass=ABCMeta):

    def __init__(self, cli_context: CLIContext) -> None:
        self.ctx = cli_context

    @abstractmethod
    def print_item(
        self,
        cli_ctx: CLIContext,
        rows: Sequence[Tuple[str, T]],
        format_row: Callable[[T], T] = _identity_func,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def print_items(
        self,
        cli_ctx: CLIContext,
        row_sets: Sequence[Sequence[Tuple[str, T]]],
        format_row: Callable[[T], T] = _identity_func,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def print_paginated_list(
        self,
        cli_ctx: CLIContext,
        fetch_func: Callable[[int, int], PaginatedResult[T]],
        initial_page_offset: int,
        page_size: int = None,
        format_item: Callable[[T], T] = _identity_func,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def print_error(
        self,
        cli_ctx: CLIContext,
        error: Exception,
    ) -> None:
        raise NotImplementedError
