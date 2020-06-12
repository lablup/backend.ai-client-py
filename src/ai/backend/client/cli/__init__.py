from pathlib import Path
import os
import signal
import sys

import click
from click.exceptions import ClickException, Abort

from .. import __version__
from ..config import APIConfig, set_config


class AliasGroup(click.Group):
    """
    Enable command aliases.

    ref) https://github.com/click-contrib/click-aliases
    """
    def __init__(self, *args, **kwargs):
        super(AliasGroup, self).__init__(*args, **kwargs)
        self._commands = {}
        self._aliases = {}

    def command(self, *args, **kwargs):
        aliases = kwargs.pop('aliases', [])
        decorator = super(AliasGroup, self).command(*args, **kwargs)
        if not aliases:
            return decorator

        def _decorator(f):
            cmd = decorator(f)
            if aliases:
                self._commands[cmd.name] = aliases
                for alias in aliases:
                    self._aliases[alias] = cmd.name
            return cmd
        return _decorator

    def group(self, *args, **kwargs):
        aliases = kwargs.pop('aliases', [])
        decorator = super(AliasGroup, self).group(*args, **kwargs)
        if not aliases:
            return decorator

        def _decorator(f):
            cmd = decorator(f)
            if aliases:
                self._commands[cmd.name] = aliases
                for alias in aliases:
                    self._aliases[alias] = cmd.name
            return cmd
        return _decorator

    def get_command(self, ctx, cmd_name):
        if cmd_name in self._aliases:
            cmd_name = self._aliases[cmd_name]
        command = super(AliasGroup, self).get_command(ctx, cmd_name)
        if command:
            return command

    def format_commands(self, ctx, formatter):
        commands = []
        for subcommand in self.list_commands(ctx):
            cmd = self.get_command(ctx, subcommand)
            # What is this, the tool lied about a command. Ignore it
            if cmd is None:
                continue
            if cmd.hidden:
                continue
            if subcommand in self._commands:
                aliases = ','.join(sorted(self._commands[subcommand]))
                subcommand = '{0} ({1})'.format(subcommand, aliases)
            commands.append((subcommand, cmd))

        # allow for 3 times the default spacing
        if len(commands):
            limit = formatter.width - 6 - max(len(cmd[0]) for cmd in commands)
            rows = []
            for subcommand, cmd in commands:
                help = cmd.get_short_help_str(limit)
                rows.append((subcommand, help))
            if rows:
                with formatter.section('Commands'):
                    formatter.write_dl(rows)


@click.group(
    cls=AliasGroup,
    context_settings={
        'help_option_names': ['-h', '--help'],
    },
)
@click.option('--skip-sslcert-validation',
              help='Skip SSL certificate validation for all API requests.',
              is_flag=True)
@click.version_option(version=__version__)
def main(skip_sslcert_validation):
    """
    Backend.AI command line interface.
    """
    from .announcement import announce
    config = APIConfig(
        skip_sslcert_validation=skip_sslcert_validation,
        announcement_handler=announce,
    )
    set_config(config)


@click.command(context_settings=dict(ignore_unknown_options=True,
                                     allow_extra_args=True))
def run_alias():
    """
    Quick aliases for run command.
    """
    mode = Path(sys.argv[0]).stem
    help = True if len(sys.argv) <= 1 else False
    if mode == 'lcc':
        sys.argv.insert(1, 'c')
    elif mode == 'lpython':
        sys.argv.insert(1, 'python')
    sys.argv.insert(1, 'run')
    if help:
        sys.argv.append('--help')
    run_main()


def _attach_command():
    from . import admin, config, app, files, logs, manager, proxy, ps, run  # noqa
    from . import vfolder       # noqa


_attach_command()


def run_main():
    try:
        _interrupted = False
        main.main(
            standalone_mode=False,
            prog_name='backend.ai',
        )
    except KeyboardInterrupt:
        # For interruptions outside the Click's exception handling block.
        print("Interrupted!", end="", file=sys.stderr)
        sys.stderr.flush()
        _interrupted = True
    except Abort as e:
        # Click wraps unhandled KeyboardInterrupt with a plain
        # sys.exit(1) call and prints "Aborted!" message
        # (which would look non-sense to users).
        # This is *NOT* what we want.
        # Instead of relying on Click, mark the _interrupted
        # flag to perform our own exit routines.
        if isinstance(e.__context__, KeyboardInterrupt):
            print("Interrupted!", end="", file=sys.stderr)
            sys.stderr.flush()
            _interrupted = True
        else:
            print("Aborted!", end="", file=sys.stderr)
            sys.stderr.flush()
            sys.exit(1)
    except ClickException as e:
        e.show()
        sys.exit(e.exit_code)
    finally:
        if _interrupted:
            # Override the exit code when it's interrupted,
            # referring https://github.com/python/cpython/pull/11862
            if sys.platform.startswith('win'):
                # Use STATUS_CONTROL_C_EXIT to notify cmd.exe
                # for interrupted exit
                sys.exit(-1073741510)
            else:
                # Use the default signal handler to set the exit
                # code properly for interruption.
                signal.signal(signal.SIGINT, signal.SIG_DFL)
                os.kill(os.getpid(), signal.SIGINT)
