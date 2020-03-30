import os
import signal
import sys

from . import main, cli_context

try:
    cli_context['running_as_cli'] = True
    main()
finally:
    if cli_context.get('interrupted', False):
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
            os.kill(0, signal.SIGINT)
