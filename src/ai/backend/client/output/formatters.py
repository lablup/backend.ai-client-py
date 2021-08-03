from __future__ import annotations

import decimal
import json
import textwrap
from typing import (
    Any,
    Mapping,
    Optional,
)

import humanize

from .types import AbstractOutputFormatter


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


class OutputFormatter(AbstractOutputFormatter):
    """
    The base implementation of output formats.
    """

    def format_console(self, value):
        if value is None:
            return "(null)"
        if isinstance(value, (dict, list, set)) and not value:
            return "(empty)"
        elif isinstance(value, dict):
            return {k: self.format_console(v) for k, v in value.items()}
        elif isinstance(value, (list, tuple, set)):
            return [self.format_console(v) for v in value]
        return str(value)

    def format_json(self, value):
        if isinstance(value, decimal.Decimal):
            return str(value)
        elif isinstance(value, dict):
            return {k: self.format_json(v) for k, v in value.items()}
        elif isinstance(value, (list, tuple)):
            return [self.format_json(v) for v in value]
        return value


class NestedDictOutputFormatter(OutputFormatter):

    def format_console(self, value):
        value = json.loads(value)
        return format_nested_dicts(value)

    def format_json(self, value):
        return json.loads(value)


class MiBytesOutputFormatter(OutputFormatter):
    def format_console(self, value):
        value = round(value / 2 ** 20, 1)
        return super().format_console(value)

    def format_json(self, value):
        value = round(value / 2 ** 20, 1)
        return super().format_json(value)


class SubFieldOutputFormatter(OutputFormatter):
    def __init__(self, subfield_name: str) -> None:
        self._subfield_name = subfield_name

    def format_console(self, value):
        return super().format_console(value[self._subfield_name])

    def format_json(self, value):
        return super().format_json(value[self._subfield_name])


class ResourceSlotFormatter(OutputFormatter):

    def format_console(self, value):
        value = json.loads(value)
        if mem := value.get('mem'):
            value['mem'] = humanize.naturalsize(mem, binary=True, gnu=True)
        return ", ".join(
            f"{k}:{v}" for k, v in value.items()
        )

    def format_json(self, value):
        return json.loads(value)


default_output_formatter = OutputFormatter()
nested_dict_formatter = NestedDictOutputFormatter()
mibytes_output_formatter = MiBytesOutputFormatter()
resource_slot_formatter = ResourceSlotFormatter()


class AgentStatFormatter(OutputFormatter):

    def format_console(self, raw_stats):
        raw_stats = json.loads(raw_stats)

        value_formatters = {
            'bytes': lambda m: "{} / {}".format(
                humanize.naturalsize(int(m['current']), binary=True),
                humanize.naturalsize(int(m['capacity']), binary=True),
            ),
            'Celsius': lambda m: "{:,} C".format(
                float(m['current']),
            ),
            'bps': lambda m: "{}/s".format(
                humanize.naturalsize(float(m['current'])),
            ),
            'pct': lambda m: "{} %".format(
                m['pct'],
            ),
        }

        def format_value(metric):
            formatter = value_formatters.get(
                metric['unit_hint'],
                lambda m: "{} / {} {}".format(
                    m['current'],
                    m['capacity'],
                    m['unit_hint'],
                ),
            )
            return formatter(metric)

        bufs = []
        node_metric_bufs = []
        for stat_key, metric in raw_stats['node'].items():
            if stat_key == 'cpu_util':
                num_cores = len(raw_stats['devices']['cpu_util'])
                if metric['pct'] is None:
                    node_metric_bufs.append(f"{stat_key}: (calculating...) % ({num_cores} cores)")
                else:
                    node_metric_bufs.append(f"{stat_key}: {metric['pct']} % ({num_cores} cores)")
            else:
                node_metric_bufs.append(f"{stat_key}: {format_value(metric)}")
        bufs.append(", ".join(node_metric_bufs))
        dev_metric_bufs = []
        for stat_key, per_dev_metric in raw_stats['devices'].items():
            dev_metric_bufs.append(f"+ {stat_key}")
            if stat_key == 'cpu_util' and len(per_dev_metric) > 8:
                dev_metric_bufs.append(
                    "  - (per-core stats hidden for large CPUs with more than 8 cores)"
                )
            else:
                for dev_id, metric in per_dev_metric.items():
                    dev_metric_bufs.append(
                        f"  - {dev_id}: {format_value(metric)}"
                    )
        bufs.append("\n".join(dev_metric_bufs))
        return '\n'.join(bufs)

    format_json = format_console


class GroupListFormatter(OutputFormatter):

    def format_console(self, value):
        return ", ".join(g['name'] for g in value)

    def format_json(self, value):
        return value


class KernelStatFormatter(OutputFormatter):

    def format_console(self, value):
        return format_stats(value)

    def format_json(self, value):
        return value


class ContainerListFormatter(OutputFormatter):

    def format_console(self, value, indent='') -> str:
        assert isinstance(value, list)
        if len(value) == 0:
            text = "- (There are no sub-containers belonging to the session)"
        else:
            text = ""
            for cinfo in value:
                text += "\n".join((
                    f"+ {cinfo['id']}",
                    *(f"  - {k + ': ':18s}{format_multiline(v, 22)}"
                    for k, v in cinfo.items()
                    if k not in ('id', 'live_stat', 'last_stat')),
                    f"  + live_stat: {format_stats(cinfo['live_stat'], indent='    ')}",
                    f"  + last_stat: {format_stats(cinfo['last_stat'], indent='    ')}",
                )) + "\n"
        return "\n" + textwrap.indent(text, indent)

    def format_json(self, value):
        return value


class DependencyListFormatter(OutputFormatter):

    def format_console(self, value, indent='') -> str:
        assert isinstance(value, list)
        if len(value) == 0:
            text = "- (There are no dependency tasks)"
        else:
            text = ""
            for dinfo in value:
                text += "\n".join(
                    (f"+ {dinfo['name']} ({dinfo['id']})",
                    *(f"  - {k + ': ':18s}{v}" for k, v in dinfo.items() if k not in ('name', 'id'))),
                )
        return "\n" + textwrap.indent(text, indent)

    def format_json(self, value):
        return value
