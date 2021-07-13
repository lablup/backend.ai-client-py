import json
import re
import textwrap
from typing import Any, Mapping, Optional

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
            self.fail(f"expected string, got {value!r} of type {type(value).__name__}", param, ctx)
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
            self.fail(f"expected string, got {value!r} of type {type(value).__name__}", param, ctx)
        m = self._rx_digits.search(value)
        if m is None:
            self.fail(f"{value!r} is not a valid byte-size expression", param, ctx)
        return value


def format_stats(raw_stats: Optional[str], indent='') -> str:
    if raw_stats is None:
        return "(unavailable)"
    stats = json.loads(raw_stats)
    text = "\n".join(f"- {k + ': ':18s}{v}" for k, v in stats.items())
    return "\n" + textwrap.indent(text, indent)


def format_multiline(value: Any, indent_length: int) -> str:
    buf = []
    for idx, line in enumerate(str(value).strip().splitlines()):
        if idx == 0:
            buf.append(line)
        else:
            buf.append((" " * indent_length) + line)
    return "\n".join(buf)


def format_nested_dicts(value: Mapping[str, Mapping[str, Any]]) -> str:
    """
    Format a mapping from string keys to sub-mappings.
    """
    rows = []
    if not value:
        rows.append("(empty)")
    else:
        for outer_key, outer_value in value.items():
            if isinstance(outer_value, dict):
                if outer_value:
                    rows.append(f"+ {outer_key}")
                    inner_rows = format_nested_dicts(outer_value)
                    rows.append(textwrap.indent(inner_rows, prefix="  "))
                else:
                    rows.append(f"+ {outer_key}: (empty)")
            else:
                if outer_value is None:
                    rows.append(f"- {outer_key}: (null)")
                else:
                    rows.append(f"- {outer_key}: {outer_value}")
    return "\n".join(rows)


def format_value(value: Any) -> str:
    if value is None:
        return "(null)"
    if isinstance(value, (dict, list, set)) and not value:
        return "(empty)"
    return str(value)
