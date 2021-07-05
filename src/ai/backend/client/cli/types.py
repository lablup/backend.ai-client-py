from __future__ import annotations

import enum
from typing import TYPE_CHECKING

import attr

if TYPE_CHECKING:
    from ..config import APIConfig


class OutputMode(enum.Enum):
    CONSOLE = 'console'
    JSON = 'json'


@attr.s(auto_attribs=True, slots=True)
class CLIContext:
    api_config: APIConfig
    output_mode: OutputMode
