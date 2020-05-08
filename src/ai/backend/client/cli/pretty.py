import enum
import functools
import io
import os
import sys
import textwrap
import traceback

from tqdm import tqdm
from click import echo, style

from ..exceptions import BackendAPIError

__all__ = (
    'PrintStatus', 'print_pretty', 'print_info', 'print_wait',
    'print_done', 'print_fail',
)


class PrintStatus(enum.Enum):
    NONE = 0
    WAITING = 1
    DONE = 2
    FAILED = 3
    WARNING = 4


def bold(text: str) -> str:
    '''
    Wraps the given text with bold enable/disable ANSI sequences.
    '''
    return (style(text, bold=True, reset=False) +
            style('', bold=False, reset=False))


def underline(text: str) -> str:
    return (style(text, underline=True, reset=False) +
            style('', underline=False, reset=False))


def inverse(text: str) -> str:
    return (style(text, reverse=True, reset=False) +
            style('', reverse=False, reset=False))


def italic(text: str) -> str:
    return '\x1b[3m' + text + '\x1b[23m'


def format_pretty(msg, status=PrintStatus.NONE, colored=True):
    if status == PrintStatus.NONE:
        indicator = style('\u2219', fg='bright_cyan', reset=False)
    elif status == PrintStatus.WAITING:
        indicator = style('\u22EF', fg='bright_yellow', reset=False)
    elif status == PrintStatus.DONE:
        indicator = style('\u2714', fg='bright_green', reset=False)
    elif status == PrintStatus.FAILED:
        indicator = style('\u2718', fg='bright_red', reset=False)
    elif status == PrintStatus.WARNING:
        indicator = style('\u2219', fg='yellow', reset=False)
    else:
        raise ValueError
    return style(indicator + textwrap.indent(msg, '  ')[1:], reset=True)


format_info = functools.partial(format_pretty, status=PrintStatus.NONE)
format_wait = functools.partial(format_pretty, status=PrintStatus.WAITING)
format_done = functools.partial(format_pretty, status=PrintStatus.DONE)
format_fail = functools.partial(format_pretty, status=PrintStatus.FAILED)
format_warn = functools.partial(format_pretty, status=PrintStatus.WARNING)


def print_pretty(msg, *, status=PrintStatus.NONE, file=None):
    if file is None:
        file = sys.stderr
    if status == PrintStatus.NONE:
        indicator = style('\u2219', fg='bright_cyan', reset=False)
    elif status == PrintStatus.WAITING:
        assert '\n' not in msg, 'Waiting message must be a single line.'
        indicator = style('\u22EF', fg='bright_yellow', reset=False)
    elif status == PrintStatus.DONE:
        indicator = style('\u2714', fg='bright_green', reset=False)
    elif status == PrintStatus.FAILED:
        indicator = style('\u2718', fg='bright_red', reset=False)
    elif status == PrintStatus.WARNING:
        indicator = style('\u2219', fg='yellow', reset=False)
    else:
        raise ValueError
    echo('\x1b[2K', nl=False, file=file)
    text = textwrap.indent(msg, '  ')
    text = style(indicator + text[1:], reset=True)
    echo('{0}\r'.format(text), nl=False, file=file)
    file.flush()
    if status != PrintStatus.WAITING:
        echo('', file=file)


print_info = functools.partial(print_pretty, status=PrintStatus.NONE)
print_wait = functools.partial(print_pretty, status=PrintStatus.WAITING)
print_done = functools.partial(print_pretty, status=PrintStatus.DONE)
print_fail = functools.partial(print_pretty, status=PrintStatus.FAILED)
print_warn = functools.partial(print_pretty, status=PrintStatus.WARNING)


def format_error(exc: Exception):
    if isinstance(exc, BackendAPIError):
        yield '{0}: {1} {2}\n'.format(exc.__class__.__name__,
                                      exc.status, exc.reason)
        yield '{0[title]}'.format(exc.data)
        other_details = exc.data.get('msg', None)
        if other_details:
            yield '\n\u279c Error details: '
            yield str(other_details)
        agent_details = exc.data.get('agent-details', None)
        if agent_details is not None:
            yield '\n\u279c This is an agent-side error. '
            yield 'Check the agent status or ask the administrator for help.'
            agent_exc = agent_details.get('exception', None)
            if agent_exc is not None:
                yield '\n\u279c ' + str(agent_exc)
            desc = agent_details.get('title', None)
            if desc is not None:
                yield '\n\u279c ' + str(desc)
        content = exc.data.get('content', None)
        if content:
            yield '\n' + content
    else:
        args = exc.args if exc.args else ['']
        yield '{0}: {1}\n'.format(exc.__class__.__name__,
                                  str(args[0]))
        yield '{}'.format('\n'.join(map(str, args[1:])))
        yield ('*** Traceback ***\n' +
               ''.join(traceback.format_tb(exc.__traceback__)).strip())


def print_error(exc: Exception, *, file=None):
    if file is None:
        file = sys.stderr
    indicator = style('\u2718', fg='bright_red', reset=False)
    if file.isatty():
        echo('\x1b[2K', nl=False, file=file)
    text = ''.join(format_error(exc))
    text = textwrap.indent(text, '  ')
    text = style(indicator + text[1:], reset=True)
    echo('{0}\r'.format(text), nl=False, file=file)
    echo('', file=file)
    file.flush()


class ProgressReportingReader(io.BufferedReader):

    def __init__(self, file_path, *, tqdm_instance=None):
        super().__init__(open(file_path, 'rb'))
        self._filename = os.path.basename(file_path)
        if tqdm_instance is None:
            self._owns_tqdm = True
            self.tqdm = tqdm(
                unit='bytes',
                unit_scale=True,
                total=os.path.getsize(file_path),
            )
        else:
            self._owns_tqdm = False
            self.tqdm = tqdm_instance

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if self._owns_tqdm:
            self.tqdm.close()
        self.close()

    def read(self, *args, **kwargs):
        chunk = super().read(*args, **kwargs)
        self.tqdm.set_postfix(file=self._filename, refresh=False)
        self.tqdm.update(len(chunk))
        return chunk

    def read1(self, *args, **kwargs):
        chunk = super().read1(*args, **kwargs)
        self.tqdm.set_postfix(file=self._filename, refresh=False)
        self.tqdm.update(len(chunk))
        return chunk

    def readinto(self, *args, **kwargs):
        count = super().readinto(*args, **kwargs)
        self.tqdm.set_postfix(file=self._filename, refresh=False)
        self.tqdm.update(count)

    def readinto1(self, *args, **kwargs):
        count = super().readinto1(*args, **kwargs)
        self.tqdm.set_postfix(file=self._filename, refresh=False)
        self.tqdm.update(count)
