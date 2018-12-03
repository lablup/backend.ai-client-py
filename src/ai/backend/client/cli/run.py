from argparse import ArgumentTypeError, Namespace
import asyncio
import collections
from decimal import Decimal
import getpass
import itertools
import json
from pathlib import Path
import re
import string
import sys
import traceback

import aiohttp
from humanize import naturalsize
from tabulate import tabulate

from . import register_command
from .admin.sessions import session
from ..compat import current_loop, token_hex
from ..exceptions import BackendError
from ..session import Session, AsyncSession
from .pretty import (
    print_info, print_wait, print_done, print_fail, print_warn,
    format_info,
)

_rx_range_key = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')


def drange(start: Decimal, stop: Decimal, num: int):
    '''
    A simplified version of numpy.linspace with default options
    '''
    delta = stop - start
    step = delta / (num - 1)
    yield from (start + step * Decimal(tick) for tick in range(0, num))


def range_expr(arg):
    '''
    Accepts a range expression which generates a range of values for a variable.

    Linear space range: "linspace:1,2,10" (start, stop, num) as in numpy.linspace
    Pythonic range: "range:1,10,2" (start, stop[, step]) as in Python's range
    Case range: "case:a,b,c" (comma-separated strings)
    '''
    key, value = arg.split('=', maxsplit=1)
    assert _rx_range_key.match(key), 'The key must be a valid slug string.'
    try:
        if value.startswith('case:'):
            return key, value[5:].split(',')
        elif value.startswith('linspace:'):
            start, stop, num = value[9:].split(',')
            return key, tuple(drange(Decimal(start), Decimal(stop), int(num)))
        elif value.startswith('range:'):
            range_args = map(int, value[6:].split(','))
            return key, tuple(range(*range_args))
        else:
            raise ArgumentTypeError('Unrecognized range expression type')
    except ValueError as e:
        raise ArgumentTypeError(str(e))


async def exec_loop(stdout, stderr, kernel, mode, code, *, opts=None,
                    vprint_done=print_done, is_multi=False):
    '''
    Fully streamed asynchronous version of the execute loop.
    '''
    async with kernel.stream_execute(code, mode=mode, opts=opts) as stream:
        async for result in stream:
            if result.type == aiohttp.WSMsgType.TEXT:
                result = json.loads(result.data)
            else:
                # future extension
                continue
            for rec in result.get('console', []):
                if rec[0] == 'stdout':
                    print(rec[1], end='', file=stdout)
                elif rec[0] == 'stderr':
                    print(rec[1], end='', file=stderr)
                else:
                    print('----- output record (type: {0}) -----'.format(rec[0]),
                          file=stdout)
                    print(rec[1], file=stdout)
                    print('----- end of record -----', file=stdout)
            stdout.flush()
            files = result.get('files', [])
            if files:
                print('--- generated files ---', file=stdout)
                for item in files:
                    print('{0}: {1}'.format(item['name'], item['url']), file=stdout)
                print('--- end of generated files ---', file=stdout)
            if result['status'] == 'clean-finished':
                exitCode = result.get('exitCode')
                msg = 'Clean finished. (exit code = {0})'.format(exitCode)
                if is_multi:
                    print(msg, file=stderr)
                vprint_done(msg)
            elif result['status'] == 'build-finished':
                exitCode = result.get('exitCode')
                msg = 'Build finished. (exit code = {0})'.format(exitCode)
                if is_multi:
                    print(msg, file=stderr)
                vprint_done(msg)
            elif result['status'] == 'finished':
                exitCode = result.get('exitCode')
                msg = 'Execution finished. (exit code = {0})'.format(exitCode)
                if is_multi:
                    print(msg, file=stderr)
                vprint_done(msg)
                break
            elif result['status'] == 'waiting-input':
                if result['options'].get('is_password', False):
                    code = getpass.getpass()
                else:
                    code = input()
                await stream.send_str(code)
            elif result['status'] == 'continued':
                pass


def exec_loop_sync(stdout, stderr, kernel, mode, code, *, opts=None,
                   vprint_done=print_done):
    '''
    Old synchronous polling version of the execute loop.
    '''
    opts = opts if opts else {}
    run_id = None  # use server-assigned run ID
    while True:
        result = kernel.execute(run_id, code, mode=mode, opts=opts)
        run_id = result['runId']
        opts.clear()  # used only once
        for rec in result['console']:
            if rec[0] == 'stdout':
                print(rec[1], end='', file=stdout)
            elif rec[0] == 'stderr':
                print(rec[1], end='', file=stderr)
            else:
                print('----- output record (type: {0}) -----'.format(rec[0]),
                      file=stdout)
                print(rec[1], file=stdout)
                print('----- end of record -----', file=stdout)
        stdout.flush()
        files = result.get('files', [])
        if files:
            print('--- generated files ---', file=stdout)
            for item in files:
                print('{0}: {1}'.format(item['name'], item['url']), file=stdout)
            print('--- end of generated files ---', file=stdout)
        if result['status'] == 'clean-finished':
            exitCode = result.get('exitCode')
            vprint_done('Clean finished. (exit code = {0}'.format(exitCode),
                        file=stdout)
            mode = 'continue'
            code = ''
        elif result['status'] == 'build-finished':
            exitCode = result.get('exitCode')
            vprint_done('Build finished. (exit code = {0})'.format(exitCode),
                        file=stdout)
            mode = 'continue'
            code = ''
        elif result['status'] == 'finished':
            exitCode = result.get('exitCode')
            vprint_done('Execution finished. (exit code = {0})'.format(exitCode),
                        file=stdout)
            break
        elif result['status'] == 'waiting-input':
            mode = 'input'
            if result['options'].get('is_password', False):
                code = getpass.getpass()
            else:
                code = input()
        elif result['status'] == 'continued':
            mode = 'continue'
            code = ''


async def exec_terminal(kernel, *,
                        vprint_wait=print_wait, vprint_done=print_done):
    # async with kernel.stream_pty() as stream: ...
    raise NotImplementedError


def _noop(*args, **kwargs):
    pass


def _format_stats(stats):
    formatted = []
    for k, v in stats.items():
        if k.endswith('_size') or k.endswith('_bytes'):
            v = naturalsize(v, binary=True)
        elif k == 'cpu_used':
            k += '_msec'
            v = '{0:,}'.format(int(v))
        else:
            v = '{0:,}'.format(int(v))
        formatted.append((k, v))
    return tabulate(formatted)


def _get_mem_slots(size, suffix):
    size = float(size)
    suffix = suffix.lower()
    if suffix in ('k', 'kb', 'kib'):
        return size / 2 ** 20
    elif suffix in ('m', 'mb', 'mib'):
        return size / 2 ** 10
    elif suffix in ('g', 'gb', 'gib'):
        return size
    elif suffix in ('t', 'tb', 'tib'):
        return size * 2 ** 10
    elif suffix in ('p', 'pb', 'pib'):
        return size * 2 ** 20
    return None


@register_command
def run(args):
    '''
    Run the given code snippet or files in a session.
    Depending on the session ID you give (default is random),
    it may reuse an existing session or create a new one.
    '''
    if args.quiet:
        vprint_info = vprint_wait = vprint_done = _noop
    else:
        vprint_info = print_info
        vprint_wait = print_wait
        vprint_done = print_done
    if args.env is not None:
        envs = {k: v for k, v in map(lambda s: s.split('=', 1), args.env)}
    else:
        envs = {}
    if args.files and args.code:
        print('You can run only either source files or command-line '
              'code snippet.', file=sys.stderr)
        sys.exit(1)
    if not args.files and not args.code:
        print('You should provide the command-line code snippet using '
              '"-c" option if run without files.', file=sys.stderr)
        sys.exit(1)
    if args.resources:
        resources = {k: v for k, v in map(lambda s: s.split('=', 1), args.resources)}
    else:
        resources = {}  # use the defaults configured in the server

    # Reverse humanized memory unit
    mem = resources.pop('mem', None)
    mem = resources.pop('ram', None) if mem is None else mem
    if mem:
        memlist = re.findall(r'[A-Za-z]+|[\d\.]+', mem)
        if memlist and len(memlist) == 2:
            memslot = _get_mem_slots(memlist[0], memlist[1])
            if memslot:
                resources['mem'] = memslot

    if not (1 <= args.cluster_size < 4):
        print('Invalid cluster size.', file=sys.stderr)
        sys.exit(1)

    if args.env_range is None: args.env_range = []      # noqa
    if args.build_range is None: args.build_range = []  # noqa
    if args.exec_range is None: args.exec_range = []    # noqa

    env_ranges = {v: r for v, r in args.env_range}
    build_ranges = {v: r for v, r in args.build_range}
    exec_ranges = {v: r for v, r in args.exec_range}

    env_var_maps = [dict(zip(env_ranges.keys(), values))
                    for values in itertools.product(*env_ranges.values())]
    build_var_maps = [dict(zip(build_ranges.keys(), values))
                      for values in itertools.product(*build_ranges.values())]
    exec_var_maps = [dict(zip(exec_ranges.keys(), values))
                     for values in itertools.product(*exec_ranges.values())]
    case_set = collections.OrderedDict()
    vmaps_product = itertools.product(env_var_maps, build_var_maps, exec_var_maps)
    build_template = string.Template(args.build)
    exec_template = string.Template(args.exec)
    env_templates = {k: string.Template(v) for k, v in envs.items()}
    for env_vmap, build_vmap, exec_vmap in vmaps_product:
        interpolated_envs = tuple((k, vt.substitute(env_vmap))
                                  for k, vt in env_templates.items())
        if args.build:
            interpolated_build = build_template.substitute(build_vmap)
        else:
            interpolated_build = '*'
        if args.exec:
            interpolated_exec = exec_template.substitute(exec_vmap)
        else:
            interpolated_exec = '*'
        case_set[(interpolated_envs, interpolated_build, interpolated_exec)] = 1

    is_multi = (len(case_set) > 1)
    if is_multi:
        if args.max_parallel <= 0:
            print('The number maximum parallel sessions must be '
                  'a positive integer.', file=sys.stderr)
            sys.exit(1)
        if args.terminal:
            print('You cannot run multiple cases with terminal.', file=sys.stderr)
            sys.exit(1)
        if not args.quiet:
            vprint_info('Running multiple sessions for the following combinations:')
            for case in case_set.keys():
                pretty_env = ' '.join('{}={}'.format(item[0], item[1])
                                      for item in case[0])
                print('env = {!r}, build = {!r}, exec = {!r}'
                      .format(pretty_env, case[1], case[2]))

    def _run_legacy(session, args, idx, session_id, envs,
                    clean_cmd, build_cmd, exec_cmd):
        try:
            kernel = session.Kernel.get_or_create(
                args.lang,
                client_token=session_id,
                cluster_size=args.cluster_size,
                mounts=args.mount,
                envs=envs,
                resources=resources,
                tag=args.tag)
        except BackendError as e:
            print_fail('[{0}] {1}'.format(idx, e))
            return
        if kernel.created:
            vprint_done('[{0}] Session {0} is ready.'.format(idx, kernel.kernel_id))
        else:
            vprint_done('[{0}] Reusing session {0}...'.format(idx, kernel.kernel_id))

        try:
            if args.files:
                vprint_wait('[{0}] Uploading source files...'.format(idx))
                ret = kernel.upload(args.files, basedir=args.basedir,
                                    show_progress=True)
                if ret.status // 100 != 2:
                    print_fail('[{0}] Uploading source files failed!'.format(idx))
                    print('{0}: {1}\n{2}'.format(
                        ret.status, ret.reason, ret.text()))
                    return
                vprint_done('[{0}] Uploading done.'.format(idx))
                opts = {
                    'clean': clean_cmd,
                    'build': build_cmd,
                    'exec': exec_cmd,
                }
                if not args.terminal:
                    exec_loop_sync(sys.stdout, sys.stderr, kernel, 'batch', '',
                                   opts=opts,
                                   vprint_done=vprint_done)
            if args.terminal:
                raise NotImplementedError('Terminal access is not supported in '
                                          'the legacy synchronous mode.')
            if args.code:
                exec_loop_sync(sys.stdout, sys.stderr, kernel, 'query', args.code,
                               vprint_done=vprint_done)
            vprint_done('[{0}] Execution finished.'.format(idx))
        except BackendError as e:
            print_fail('[{0}] {1}'.format(idx, e))
            sys.exit(1)
        except Exception:
            print_fail('[{0}] Execution failed!'.format(idx))
            traceback.print_exc()
            sys.exit(1)
        finally:
            if args.rm:
                vprint_wait('[{0}] Cleaning up the session...'.format(idx))
                ret = kernel.destroy()
                vprint_done('[{0}] Cleaned up the session.'.format(idx))
                if args.stats:
                    stats = ret.get('stats', None) if ret else None
                    if stats:
                        print('[{0}] Statistics:\n{1}'
                              .format(idx, _format_stats(stats)))
                    else:
                        print('[{0}] Statistics is not available.'.format(idx))

    async def _run(session, args, idx, session_id, envs,
                   clean_cmd, build_cmd, exec_cmd,
                   is_multi=False):
        try:
            kernel = await session.Kernel.get_or_create(
                args.lang,
                client_token=session_id,
                cluster_size=args.cluster_size,
                mounts=args.mount,
                envs=envs,
                resources=resources,
                tag=args.tag)
        except BackendError as e:
            print_fail('[{0}] {1}'.format(idx, e))
            return
        if kernel.created:
            vprint_done('[{0}] Session {1} is ready.'.format(idx, kernel.kernel_id))
        else:
            vprint_done('[{0}] Reusing session {1}...'.format(idx, kernel.kernel_id))

        if not is_multi:
            stdout = sys.stdout
            stderr = sys.stderr
        else:
            log_dir = Path.home() / '.cache' / 'backend.ai' / 'client-logs'
            log_dir.mkdir(parents=True, exist_ok=True)
            stdout = open(log_dir / '{0}.stdout.log'.format(session_id),
                          'w', encoding='utf-8')
            stderr = open(log_dir / '{0}.stderr.log'.format(session_id),
                          'w', encoding='utf-8')

        try:
            def indexed_vprint_done(msg):
                vprint_done('[{0}] '.format(idx) + msg)
            if args.files:
                if not is_multi:
                    vprint_wait('[{0}] Uploading source files...'.format(idx))
                ret = await kernel.upload(args.files, basedir=args.basedir,
                                          show_progress=not is_multi)
                if ret.status // 100 != 2:
                    print_fail('[{0}] Uploading source files failed!'.format(idx))
                    print('{0}: {1}\n{2}'.format(
                        ret.status, ret.reason, ret.text()), file=stderr)
                    raise RuntimeError('Uploading source files has failed!')
                if not is_multi:
                    vprint_done('[{0}] Uploading done.'.format(idx))
                opts = {
                    'clean': clean_cmd,
                    'build': build_cmd,
                    'exec': exec_cmd,
                }
                if not args.terminal:
                    await exec_loop(stdout, stderr, kernel, 'batch', '',
                                    opts=opts,
                                    vprint_done=indexed_vprint_done,
                                    is_multi=is_multi)
            if args.terminal:
                await exec_terminal(kernel)
                return
            if args.code:
                await exec_loop(stdout, stderr, kernel, 'query', args.code,
                                vprint_done=indexed_vprint_done,
                                is_multi=is_multi)
        except BackendError as e:
            print_fail('[{0}] {1}'.format(idx, e))
            raise RuntimeError(e)
        except Exception as e:
            print_fail('[{0}] Execution failed!'.format(idx))
            traceback.print_exc()
            raise RuntimeError(e)
        finally:
            try:
                if args.rm:
                    if not is_multi:
                        vprint_wait('[{0}] Cleaning up the session...'.format(idx))
                    ret = await kernel.destroy()
                    vprint_done('[{0}] Cleaned up the session.'.format(idx))
                    if args.stats:
                        stats = ret.get('stats', None) if ret else None
                        if stats:
                            stats_str = _format_stats(stats)
                            print(format_info('[{0}] Statistics:'.format(idx)) +
                                  '\n{0}'.format(stats_str))
                            if is_multi:
                                print('Statistics:\n{0}'.format(stats_str),
                                      file=stderr)
                        else:
                            print_warn('[{0}] Statistics: unavailable.'.format(idx))
                            if is_multi:
                                print('Statistics: unavailable.', file=stderr)
            finally:
                if is_multi:
                    stdout.close()
                    stderr.close()

    def _run_cases_legacy():
        if args.session_id is None:
            session_id_prefix = token_hex(5)
        else:
            session_id_prefix = args.session_id
        vprint_info('Session token prefix: {0}'.format(session_id_prefix))
        vprint_info('In the legacy mode, all cases will run serially!')
        with Session() as session:
            for idx, case in enumerate(case_set.keys()):
                if is_multi:
                    session_id = '{0}-{1}'.format(session_id_prefix, idx)
                else:
                    session_id = session_id_prefix
                envs = dict(case[0])
                clean_cmd = args.clean if args.clean else '*'
                build_cmd = case[1]
                exec_cmd = case[2]
                _run_legacy(session, args, idx, session_id, envs,
                            clean_cmd, build_cmd, exec_cmd)

    async def _run_cases():
        loop = current_loop()
        if args.session_id is None:
            session_id_prefix = token_hex(5)
        else:
            session_id_prefix = args.session_id
        vprint_info('Session token prefix: {0}'.format(session_id_prefix))
        if is_multi:
            print_info('Check out the stdout/stderr logs stored in '
                       '~/.cache/backend.ai/client-logs directory.')
        async with AsyncSession() as session:
            tasks = []
            # TODO: limit max-parallelism using aiojobs
            for idx, case in enumerate(case_set.keys()):
                if is_multi:
                    session_id = '{0}-{1}'.format(session_id_prefix, idx)
                else:
                    session_id = session_id_prefix
                envs = dict(case[0])
                clean_cmd = args.clean if args.clean else '*'
                build_cmd = case[1]
                exec_cmd = case[2]
                t = loop.create_task(
                    _run(session, args, idx, session_id, envs,
                         clean_cmd, build_cmd, exec_cmd,
                         is_multi=is_multi))
                tasks.append(t)
            results = await asyncio.gather(*tasks, return_exceptions=True)
            if any(map(lambda r: isinstance(r, Exception), results)):
                if is_multi:
                    print_fail('There were failed cases!')
                sys.exit(1)

    if args.legacy:
        _run_cases_legacy()
    else:
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(_run_cases())
        finally:
            loop.close()


run.add_argument('lang',
                 help='The runtime or programming language name')
run.add_argument('files', nargs='*', type=Path,
                 help='The code file(s). Can be added multiple times')
run.add_argument('-t', '--session-id', '--client-token', metavar='SESSID',
                 help='Specify a human-readable session ID or name. '
                      'If not set, a random hex string is used.')
run.add_argument('--cluster-size', metavar='NUMBER', type=int, default=1,
                 help='The size of cluster in number of containers.')
run.add_argument('-c', '--code', metavar='CODE',
                 help='The code snippet as a single string')
run.add_argument('--clean', metavar='CMD',
                 help='Custom shell command for cleaning up the base directory')
run.add_argument('--build', metavar='CMD',
                 help='Custom shell command for building the given files')
run.add_argument('--exec', metavar='CMD',
                 help='Custom shell command for executing the given files')
run.add_argument('--terminal', action='store_true', default=False,
                 help='Connect to the terminal-type kernel.')
run.add_argument('--basedir', metavar='PATH', type=Path, default=None,
                 help='Base directory path of uploaded files.  '
                      'All uploaded files must reside inside this directory.')
run.add_argument('--rm', action='store_true', default=False,
                 help='Terminate the session immediately after running '
                      'the given code or files')
run.add_argument('-e', '--env', metavar='KEY=VAL', type=str, action='append',
                 help='Environment variable '
                      '(may appear multiple times)')
run.add_argument('--env-range', metavar='RANGE_EXPR', action='append',
                 type=range_expr,
                 help='Range expression for environment variable.')
run.add_argument('--build-range', metavar='RANGE_EXPR', action='append',
                 type=range_expr,
                 help='Range expression for execution arguments.')
run.add_argument('--exec-range', metavar='RANGE_EXPR', action='append',
                 type=range_expr,
                 help='Range expression for execution arguments.')
run.add_argument('--max-parallel', metavar='NUM', type=int, default=2,
                 help='The maximum number of parallel sessions.')
run.add_argument('-m', '--mount', type=str, action='append',
                 help='User-owned virtual folder names to mount')
run.add_argument('-s', '--stats', action='store_true', default=False,
                 help='Show resource usage statistics after termination '
                      '(only works if "--rm" is given)')
run.add_argument('--tag', type=str, default=None,
                 help='User-defined tag string to annotate sessions.')
run.add_argument('-r', '--resources', metavar='KEY=VAL', type=str, action='append',
                 help='Set computation resources (e.g: -r cpu=2 -r mem=0.2 -r gpu=1)'
                 '. 1 slot of cpu/gpu represents 1 core. The unit of mem(ory) '
                 'is GiB.')
run.add_argument('-q', '--quiet', action='store_true', default=False,
                 help='Hide execution details but show only the kernel outputs.')
run.add_argument('--legacy', action='store_true', default=False,
                 help='Use the legacy synchronous polling mode to '
                      'fetch console outputs.')


@register_command(aliases=['rm', 'kill'])
def terminate(args):
    '''
    Terminate the given session.
    '''
    print_wait('Terminating the session(s)...')
    with Session() as session:
        has_failure = False
        for sess in args.sess_id_or_alias:
            try:
                kernel = session.Kernel(sess)
                ret = kernel.destroy()
            except BackendError as e:
                print_fail(str(e))
                has_failure = True
            if has_failure:
                sys.exit(1)
        else:
            print_done('Done.')
            if args.stats:
                stats = ret.get('stats', None) if ret else None
                if stats:
                    print(_format_stats(stats))
                else:
                    print('Statistics is not available.')


terminate.add_argument('sess_id_or_alias', metavar='NAME', nargs='+',
                       help='The session ID or its alias '
                            'given when creating the session.')
terminate.add_argument('-s', '--stats', action='store_true', default=False,
                       help='Show resource usage statistics after termination')


@register_command
def info(args):
    '''
    Show detailed information for a running compute session.
    This is an alias of the "admin session <sess_id>" command.
    '''
    inner_args = Namespace()
    inner_args.sess_id_or_alias = args.sess_id_or_alias
    session(inner_args)


info.add_argument('sess_id_or_alias', metavar='NAME',
                  help='The session ID or its alias '
                       'given when creating the session.')
