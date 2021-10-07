import json
import re
from typing import (
    Any,
    Optional,
)

import click


class ByteSizeParamType(click.ParamType):
    name = "byte"

    _rx_digits = re.compile(r'^(\d+(?:\.\d*)?)([kmgtpe]?)$', re.I)
    _scales = {
        'k': 2 ** 10,
        'm': 2 ** 20,
        'g': 2 ** 30,
        't': 2 ** 40,
        'p': 2 ** 50,
        'e': 2 ** 60,
    }

    def convert(self, value, param, ctx):
        if isinstance(value, int):
            return value
        if not isinstance(value, str):
            self.fail(
                f"expected string, got {value!r} of type {type(value).__name__}",
                param, ctx,
            )
        m = self._rx_digits.search(value)
        if m is None:
            self.fail(f"{value!r} is not a valid byte-size expression", param, ctx)
        size = float(m.group(1))
        unit = m.group(2).lower()
        return int(size * self._scales.get(unit, 1))


class ByteSizeParamCheckType(ByteSizeParamType):
    name = "byte-check"

    def convert(self, value, param, ctx):
        if isinstance(value, int):
            return value
        if not isinstance(value, str):
            self.fail(
                f"expected string, got {value!r} of type {type(value).__name__}",
                param, ctx,
            )
        m = self._rx_digits.search(value)
        if m is None:
            self.fail(f"{value!r} is not a valid byte-size expression", param, ctx)
        return value


class JSONParamType(click.ParamType):
    """
    A JSON string parameter type.
    The default value must be given as a valid JSON-parsable string,
    not the Python objects.
    """

    name = "json-string"

    def __init__(self) -> None:
        super().__init__()
        self._parsed = False

    def convert(
        self,
        value: Optional[str],
        param: Optional[click.Parameter],
        ctx: Optional[click.Context],
    ) -> Any:
        if self._parsed:
            # Click invokes this method TWICE
            # for a default value given as string.
            return value
        self._parsed = True
        if value is None:
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            self.fail(f"cannot parse {value!r} as JSON", param, ctx)
        return value
