import re

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
        if not isinstance(value, str):
            self.fail(f"expected string, got {value!r} of type {type(value).__name__}", param, ctx)
        m = self._rx_digits.search(value)
        if m is None:
            self.fail(f"{value!r} is not a valid byte-size expression", param, ctx)
        return value
