import enum
import functools
import io
import os
import sys
import textwrap

from tqdm import tqdm

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


def format_pretty(msg, status=PrintStatus.NONE, colored=True):
    if status == PrintStatus.NONE:
        indicator = '\x1b[96m\u2219' if colored else '\u2219'
    elif status == PrintStatus.WAITING:
        indicator = '\x1b[93m\u22EF' if colored else '\u22EF'
    elif status == PrintStatus.DONE:
        indicator = '\x1b[92m\u2714' if colored else '\u2714'
    elif status == PrintStatus.FAILED:
        indicator = '\x1b[91m\u2718' if colored else '\u2718'
    elif status == PrintStatus.WARNING:
        indicator = '\x1b[33m\u2219' if colored else '\u2219'
    else:
        raise ValueError
    clear = '\x1b[0m' if colored else ''
    return indicator + textwrap.indent(msg, '  ')[1:] + clear


format_info = functools.partial(format_pretty, status=PrintStatus.NONE)
format_wait = functools.partial(format_pretty, status=PrintStatus.WAITING)
format_done = functools.partial(format_pretty, status=PrintStatus.DONE)
format_fail = functools.partial(format_pretty, status=PrintStatus.FAILED)
format_warn = functools.partial(format_pretty, status=PrintStatus.WARNING)


def print_pretty(msg, *, status=PrintStatus.NONE, file=None):
    if file is None:
        file = sys.stderr
    if status == PrintStatus.NONE:
        indicator = '\x1b[96m\u2219' if file.isatty() else '\u2219'
    elif status == PrintStatus.WAITING:
        assert '\n' not in msg, 'Waiting message must be a single line.'
        indicator = '\x1b[93m\u22EF' if file.isatty() else '\u22EF'
    elif status == PrintStatus.DONE:
        indicator = '\x1b[92m\u2714' if file.isatty() else '\u2714'
    elif status == PrintStatus.FAILED:
        indicator = '\x1b[91m\u2718' if file.isatty() else '\u2718'
    elif status == PrintStatus.WARNING:
        indicator = '\x1b[33m\u2219' if file.isatty() else '\u2219'
    else:
        raise ValueError
    if file.isatty():
        print('\x1b[2K', end='', file=file)
    text = textwrap.indent(msg, '  ')
    text = indicator + text[1:]
    if file.isatty():
        text += '\x1b[0m'
    print('{0}\r'.format(text), end='', file=file)
    file.flush()
    if status != PrintStatus.WAITING:
        print('', file=file)


print_info = functools.partial(print_pretty, status=PrintStatus.NONE)
print_wait = functools.partial(print_pretty, status=PrintStatus.WAITING)
print_done = functools.partial(print_pretty, status=PrintStatus.DONE)
print_fail = functools.partial(print_pretty, status=PrintStatus.FAILED)
print_warn = functools.partial(print_pretty, status=PrintStatus.WARNING)


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
