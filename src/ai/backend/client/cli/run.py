import asyncio
import collections
from decimal import Decimal
import getpass
import itertools
import json
import re
import string
import sys
import traceback

import aiohttp
import click
from humanize import naturalsize
import tabulate as tabulate_mod
from tabulate import tabulate

from . import main
from .admin.sessions import session as cli_admin_session
from ..config import local_cache_path
from ..compat import current_loop, token_hex
from ..exceptions import BackendError, BackendAPIError
from ..session import Session, AsyncSession, is_legacy_server
from .pretty import (
    print_info, print_wait, print_done, print_error, print_fail, print_warn,
    format_info,
)

_rx_range_key = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')

tabulate_mod.PRESERVE_WHITESPACE = True


def drange(start: Decimal, stop: Decimal, num: int):
    '''
    A simplified version of numpy.linspace with default options
    '''
    delta = stop - start
    step = delta / (num - 1)
    yield from (start + step * Decimal(tick) for tick in range(0, num))


class RangeExprOptionType(click.ParamType):
    '''
    Accepts a range expression which generates a range of values for a variable.

    Linear space range: "linspace:1,2,10" (start, stop, num) as in numpy.linspace
    Pythonic range: "range:1,10,2" (start, stop[, step]) as in Python's range
    Case range: "case:a,b,c" (comma-separated strings)
    '''

    name = 'Range Expression'

    def convert(self, arg, param, ctx):
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
                self.fail('Unrecognized range expression type', param, ctx)
        except ValueError as e:
            self.fail(str(e), param, ctx)


range_expr = RangeExprOptionType()


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
    version = stats.pop('version', 1)
    stats.pop('status')
    if version == 1:
        stats.pop('precpu_used', None)
        stats.pop('precpu_system_used', None)
        stats.pop('cpu_system_used', None)
        for key, val in stats.items():
            if key.endswith('_size') or key.endswith('_bytes'):
                val = naturalsize(val, binary=True)
            elif key == 'cpu_used':
                key += '_msec'
                val = '{0:,}'.format(int(val))
            else:
                val = '{0:,}'.format(int(val))
            formatted.append((key, val))
    elif version == 2:
        max_integer_len = 0
        max_fraction_len = 0
        for key, metric in stats.items():
            unit = metric['unit_hint']
            if unit == 'bytes':
                val = metric.get('stats.max', metric['current'])
                val = naturalsize(val, binary=True)
                val, unit = val.rsplit(' ', maxsplit=1)
                val = '{:,}'.format(Decimal(val))
            elif unit == 'msec':
                val = '{:,}'.format(Decimal(metric['current']))
                unit = 'msec'
            elif unit == 'percent':
                val = metric['pct']
                unit = '%'
            else:
                val = metric['current']
                unit = ''
            ip, _, fp = val.partition('.')
            max_integer_len = max(len(ip), max_integer_len)
            max_fraction_len = max(len(fp), max_fraction_len)
            formatted.append([key, val, unit])
        fstr_int_only = '{0:>' + str(max_integer_len) + '}'
        fstr_float = '{0:>' + str(max_integer_len) + '}.{1:<' + str(max_fraction_len) + '}'
        for item in formatted:
            ip, _, fp = item[1].partition('.')
            if fp == '':
                item[1] = fstr_int_only.format(ip) + ' ' * (max_fraction_len + 1)
            else:
                item[1] = fstr_float.format(ip, fp)
    else:
        print_warn('Unsupported statistics result version. Upgrade your client.')
    return tabulate(formatted)


def _prepare_resource_arg(resources):
    if resources:
        resources = {k: v for k, v in map(lambda s: s.split('=', 1), resources)}
    else:
        resources = {}  # use the defaults configured in the server
    return resources


def _prepare_env_arg(env):
    if env is not None:
        envs = {k: v for k, v in map(lambda s: s.split('=', 1), env)}
    else:
        envs = {}
    return envs


def _prepare_mount_arg(mount):
    return list(mount)


@main.command()
@click.argument('image', type=str)
@click.argument('files', nargs=-1, type=click.Path())
@click.option('-t', '--session-id', '--client-token', metavar='SESSID',
              help='Specify a human-readable session ID or name. '
                   'If not set, a random hex string is used.')
# job scheduling options
@click.option('--type', metavar='SESSTYPE',
              type=click.Choice(['batch', 'interactive']),
              default='interactive',
              help='Either batch or interactive')
@click.option('--enqueue-only', is_flag=True,
              help='Enqueue the session and return immediately without waiting for its startup.')
@click.option('--max-wait', metavar='SECONDS', type=int, default=0,
              help='The maximum duration to wait until the session starts.')
@click.option('--no-reuse', is_flag=True,
              help='Do not reuse existing sessions but return an error.')
# query-mode options
@click.option('-c', '--code', metavar='CODE',
              help='The code snippet as a single string')
@click.option('--terminal', is_flag=True,
              help='Connect to the terminal-type kernel.')
# batch-mode options
@click.option('--clean', metavar='CMD',
              help='Custom shell command for cleaning up the base directory')
@click.option('--build', metavar='CMD',
              help='Custom shell command for building the given files')
@click.option('--exec', metavar='CMD',
              help='Custom shell command for executing the given files')
@click.option('--basedir', metavar='PATH', type=click.Path(), default=None,
              help='Base directory path of uploaded files. '
                   'All uploaded files must reside inside this directory.')
# execution environment
@click.option('-e', '--env', metavar='KEY=VAL', type=str, multiple=True,
              help='Environment variable (may appear multiple times)')
# extra options
@click.option('--rm', is_flag=True,
              help='Terminate the session immediately after running '
                   'the given code or files')
@click.option('-s', '--stats', is_flag=True,
              help='Show resource usage statistics after termination '
                   '(only works if "--rm" is given)')
@click.option('--tag', type=str, default=None,
              help='User-defined tag string to annotate sessions.')
@click.option('-q', '--quiet', is_flag=True,
              help='Hide execution details but show only the kernel outputs.')
# experiment support
@click.option('--env-range', metavar='RANGE_EXPR', multiple=True,
              type=range_expr, help='Range expression for environment variable.')
@click.option('--build-range', metavar='RANGE_EXPR', multiple=True,
              type=range_expr, help='Range expression for execution arguments.')
@click.option('--exec-range', metavar='RANGE_EXPR', multiple=True, type=range_expr,
              help='Range expression for execution arguments.')
@click.option('--max-parallel', metavar='NUM', type=int, default=2,
              help='The maximum number of parallel sessions.')
# resource spec
@click.option('-m', '--mount', type=str, multiple=True,
              help='User-owned virtual folder names to mount')
@click.option('--scaling-group', '--sgroup', type=str, default=None,
              help='The scaling group to execute session. If not specified, '
                   'all available scaling groups are included in the scheduling.')
@click.option('-r', '--resources', '--resource', metavar='KEY=VAL', type=str, multiple=True,
              help='Set computation resources '
                   '(e.g: -r cpu=2 -r mem=256 -r cuda.device=1)')
@click.option('--cluster-size', metavar='NUMBER', type=int, default=1,
              help='The size of cluster in number of containers.')
@click.option('--resource-opts', metavar='KEY=VAL', type=str, multiple=True,
              help='Resource options for creating compute session. '
                   '(e.g: shmem=64m)')
# resource grouping
@click.option('-d', '--domain', metavar='DOMAIN_NAME', default=None,
              help='Domain name where the session will be spawned. '
                   'If not specified, config\'s domain name will be used.')
@click.option('-g', '--group', metavar='GROUP_NAME', default=None,
              help='Group name where the session is spawned. '
                   'User should be a member of the group to execute the code.')
def run(image, files, session_id,                          # base args
        type, enqueue_only, max_wait, no_reuse,            # job scheduling options
        code, terminal,                                    # query-mode options
        clean, build, exec, basedir,                       # batch-mode options
        env,                                               # execution environment
        rm, stats, tag, quiet,                             # extra options
        env_range, build_range, exec_range, max_parallel,  # experiment support
        mount, scaling_group, resources, cluster_size,     # resource spec
        resource_opts,
        domain, group):                                    # resource grouping
    '''
    Run the given code snippet or files in a session.
    Depending on the session ID you give (default is random),
    it may reuse an existing session or create a new one.

    \b
    IMAGE: The name (and version/platform tags appended after a colon) of session
          runtime or programming language.')
    FILES: The code file(s). Can be added multiple times.
    '''
    if quiet:
        vprint_info = vprint_wait = vprint_done = _noop
    else:
        vprint_info = print_info
        vprint_wait = print_wait
        vprint_done = print_done
    if files and code:
        print('You can run only either source files or command-line '
              'code snippet.', file=sys.stderr)
        sys.exit(1)
    if not files and not code:
        print('You should provide the command-line code snippet using '
              '"-c" option if run without files.', file=sys.stderr)
        sys.exit(1)

    envs = _prepare_env_arg(env)
    resources = _prepare_resource_arg(resources)
    resource_opts = _prepare_resource_arg(resource_opts)
    mount = _prepare_mount_arg(mount)

    if not (1 <= cluster_size < 4):
        print('Invalid cluster size.', file=sys.stderr)
        sys.exit(1)

    if env_range is None: env_range = []      # noqa
    if build_range is None: build_range = []  # noqa
    if exec_range is None: exec_range = []    # noqa

    env_ranges = {v: r for v, r in env_range}
    build_ranges = {v: r for v, r in build_range}
    exec_ranges = {v: r for v, r in exec_range}

    env_var_maps = [dict(zip(env_ranges.keys(), values))
                    for values in itertools.product(*env_ranges.values())]
    build_var_maps = [dict(zip(build_ranges.keys(), values))
                      for values in itertools.product(*build_ranges.values())]
    exec_var_maps = [dict(zip(exec_ranges.keys(), values))
                     for values in itertools.product(*exec_ranges.values())]
    case_set = collections.OrderedDict()
    vmaps_product = itertools.product(env_var_maps, build_var_maps, exec_var_maps)
    build_template = string.Template(build)
    exec_template = string.Template(exec)
    env_templates = {k: string.Template(v) for k, v in envs.items()}
    for env_vmap, build_vmap, exec_vmap in vmaps_product:
        interpolated_envs = tuple((k, vt.substitute(env_vmap))
                                  for k, vt in env_templates.items())
        if build:
            interpolated_build = build_template.substitute(build_vmap)
        else:
            interpolated_build = '*'
        if exec:
            interpolated_exec = exec_template.substitute(exec_vmap)
        else:
            interpolated_exec = '*'
        case_set[(interpolated_envs, interpolated_build, interpolated_exec)] = 1

    is_multi = (len(case_set) > 1)
    if is_multi:
        if max_parallel <= 0:
            print('The number maximum parallel sessions must be '
                  'a positive integer.', file=sys.stderr)
            sys.exit(1)
        if terminal:
            print('You cannot run multiple cases with terminal.', file=sys.stderr)
            sys.exit(1)
        if not quiet:
            vprint_info('Running multiple sessions for the following combinations:')
            for case in case_set.keys():
                pretty_env = ' '.join('{}={}'.format(item[0], item[1])
                                      for item in case[0])
                print('env = {!r}, build = {!r}, exec = {!r}'
                      .format(pretty_env, case[1], case[2]))

    def _run_legacy(session, idx, session_id, envs,
                    clean_cmd, build_cmd, exec_cmd):
        try:
            kernel = session.Kernel.get_or_create(
                image,
                client_token=session_id,
                type_=type,
                enqueue_only=enqueue_only,
                max_wait=max_wait,
                no_reuse=no_reuse,
                cluster_size=cluster_size,
                mounts=mount,
                envs=envs,
                resources=resources,
                domain_name=domain,
                group_name=group,
                scaling_group=scaling_group,
                tag=tag)
        except Exception as e:
            print_error(e)
            sys.exit(1)
        if kernel.status == 'PENDING':
            print_info('Session ID {0} is enqueued for scheduling.'
                       .format(session_id))
            return
        elif kernel.status == 'RUNNING':
            if kernel.created:
                vprint_done('[{0}] Session {1} is ready (domain={2}, group={3}).'
                            .format(idx, kernel.kernel_id, kernel.domain, kernel.group))
            else:
                vprint_done('[{0}] Reusing session {1}...'.format(idx, kernel.kernel_id))
        elif kernel.status == 'TERMINATED':
            print_warn('Session ID {0} is already terminated.\n'
                       'This may be an error in the kernel image.'
                       .format(session_id))
            return
        elif kernel.status == 'TIMEOUT':
            print_info('Session ID {0} is still on the job queue.'
                       .format(session_id))
            return
        elif kernel.status in ('ERROR', 'CANCELLED'):
            print_fail('Session ID {0} has an error during scheduling/startup or cancelled.'
                       .format(session_id))
            return

        try:
            if files:
                vprint_wait('[{0}] Uploading source files...'.format(idx))
                ret = kernel.upload(files, basedir=basedir,
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
                if not terminal:
                    exec_loop_sync(sys.stdout, sys.stderr, kernel, 'batch', '',
                                   opts=opts,
                                   vprint_done=vprint_done)
            if terminal:
                raise NotImplementedError('Terminal access is not supported in '
                                          'the legacy synchronous mode.')
            if code:
                exec_loop_sync(sys.stdout, sys.stderr, kernel, 'query', code,
                               vprint_done=vprint_done)
            vprint_done('[{0}] Execution finished.'.format(idx))
        except Exception as e:
            print_error(e)
            sys.exit(1)
        finally:
            if rm:
                vprint_wait('[{0}] Cleaning up the session...'.format(idx))
                ret = kernel.destroy()
                vprint_done('[{0}] Cleaned up the session.'.format(idx))
                if stats:
                    _stats = ret.get('stats', None) if ret else None
                    if _stats:
                        print('[{0}] Statistics:\n{1}'
                              .format(idx, _format_stats(_stats)))
                    else:
                        print('[{0}] Statistics is not available.'.format(idx))

    async def _run(session, idx, session_id, envs,
                   clean_cmd, build_cmd, exec_cmd,
                   is_multi=False):
        try:
            kernel = await session.Kernel.get_or_create(
                image,
                client_token=session_id,
                type_=type,
                enqueue_only=enqueue_only,
                max_wait=max_wait,
                no_reuse=no_reuse,
                cluster_size=cluster_size,
                mounts=mount,
                envs=envs,
                resources=resources,
                resource_opts=resource_opts,
                domain_name=domain,
                group_name=group,
                scaling_group=scaling_group,
                tag=tag)
        except Exception as e:
            print_fail('[{0}] {1}'.format(idx, e))
            return
        if kernel.status == 'PENDING':
            print_info('Session ID {0} is enqueued for scheduling.'
                       .format(session_id))
            return
        elif kernel.status == 'RUNNING':
            if kernel.created:
                vprint_done('[{0}] Session {1} is ready (domain={2}, group={3}).'
                            .format(idx, kernel.kernel_id, kernel.domain, kernel.group))
            else:
                vprint_done('[{0}] Reusing session {1}...'.format(idx, kernel.kernel_id))
        elif kernel.status == 'TERMINATED':
            print_warn('Session ID {0} is already terminated.\n'
                       'This may be an error in the kernel image.'
                       .format(session_id))
            return
        elif kernel.status == 'TIMEOUT':
            print_info('Session ID {0} is still on the job queue.'
                       .format(session_id))
            return
        elif kernel.status in ('ERROR', 'CANCELLED'):
            print_fail('Session ID {0} has an error during scheduling/startup or cancelled.'
                       .format(session_id))
            return

        if not is_multi:
            stdout = sys.stdout
            stderr = sys.stderr
        else:
            log_dir = local_cache_path / 'client-logs'
            log_dir.mkdir(parents=True, exist_ok=True)
            stdout = open(log_dir / '{0}.stdout.log'.format(session_id),
                          'w', encoding='utf-8')
            stderr = open(log_dir / '{0}.stderr.log'.format(session_id),
                          'w', encoding='utf-8')

        try:
            def indexed_vprint_done(msg):
                vprint_done('[{0}] '.format(idx) + msg)
            if files:
                if not is_multi:
                    vprint_wait('[{0}] Uploading source files...'.format(idx))
                ret = await kernel.upload(files, basedir=basedir,
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
                if not terminal:
                    await exec_loop(stdout, stderr, kernel, 'batch', '',
                                    opts=opts,
                                    vprint_done=indexed_vprint_done,
                                    is_multi=is_multi)
            if terminal:
                await exec_terminal(kernel)
                return
            if code:
                await exec_loop(stdout, stderr, kernel, 'query', code,
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
                if rm:
                    if not is_multi:
                        vprint_wait('[{0}] Cleaning up the session...'.format(idx))
                    ret = await kernel.destroy()
                    vprint_done('[{0}] Cleaned up the session.'.format(idx))
                    if stats:
                        _stats = ret.get('stats', None) if ret else None
                        if _stats:
                            stats_str = _format_stats(_stats)
                            print(format_info('[{0}] Statistics:'.format(idx)) +
                                  '\n{0}'.format(stats_str))
                            if is_multi:
                                print('Statistics:\n{0}'.format(stats_str),
                                      file=stderr)
                        else:
                            print_warn('[{0}] Statistics: unavailable.'.format(idx))
                            if is_multi:
                                print('Statistics: unavailable.', file=stderr)
            except Exception as e:
                print_fail('[{0}] Error while printing stats'.format(idx))
                traceback.print_exc()
                raise RuntimeError(e)
            finally:
                if is_multi:
                    stdout.close()
                    stderr.close()

    def _run_cases_legacy():
        if session_id is None:
            session_id_prefix = token_hex(5)
        else:
            session_id_prefix = session_id
        vprint_info('Session token prefix: {0}'.format(session_id_prefix))
        vprint_info('In the legacy mode, all cases will run serially!')
        with Session() as session:
            for idx, case in enumerate(case_set.keys()):
                if is_multi:
                    _session_id = '{0}-{1}'.format(session_id_prefix, idx)
                else:
                    _session_id = session_id_prefix
                envs = dict(case[0])
                clean_cmd = clean if clean else '*'
                build_cmd = case[1]
                exec_cmd = case[2]
                _run_legacy(session, idx, _session_id, envs,
                            clean_cmd, build_cmd, exec_cmd)

    async def _run_cases():
        loop = current_loop()
        if session_id is None:
            session_id_prefix = token_hex(5)
        else:
            session_id_prefix = session_id
        vprint_info('Session token prefix: {0}'.format(session_id_prefix))
        if is_multi:
            print_info('Check out the stdout/stderr logs stored in '
                       '~/.cache/backend.ai/client-logs directory.')
        async with AsyncSession() as session:
            tasks = []
            # TODO: limit max-parallelism using aiojobs
            for idx, case in enumerate(case_set.keys()):
                if is_multi:
                    _session_id = '{0}-{1}'.format(session_id_prefix, idx)
                else:
                    _session_id = session_id_prefix
                envs = dict(case[0])
                clean_cmd = clean if clean else '*'
                build_cmd = case[1]
                exec_cmd = case[2]
                t = loop.create_task(
                    _run(session, idx, _session_id, envs,
                         clean_cmd, build_cmd, exec_cmd,
                         is_multi=is_multi))
                tasks.append(t)
            results = await asyncio.gather(*tasks, return_exceptions=True)
            if any(map(lambda r: isinstance(r, Exception), results)):
                if is_multi:
                    print_fail('There were failed cases!')
                sys.exit(1)

    try:
        if is_legacy_server():
            _run_cases_legacy()
        else:
            loop = asyncio.get_event_loop()
            try:
                loop.run_until_complete(_run_cases())
            finally:
                loop.stop()
    except Exception as e:
        print_fail('{0}'.format(e))


@main.command()
@click.argument('image')
@click.option('-t', '--session-id', '--client-token', metavar='SESSID',
              help='Specify a human-readable session ID or name. '
                   'If not set, a random hex string is used.')
@click.option('-o', '--owner', '--owner-access-key', metavar='ACCESS_KEY',
              help='Set the owner of the target session explicitly.')
# job scheduling options
@click.option('--type', metavar='SESSTYPE',
              type=click.Choice(['batch', 'interactive']),
              default='interactive',
              help='Either batch or interactive')
@click.option('-c', '--startup-command', metavar='COMMAND',
              default='Set the command to execute for batch-type sessions.')
@click.option('--enqueue-only', is_flag=True,
              help='Enqueue the session and return immediately without waiting for its startup.')
@click.option('--max-wait', metavar='SECONDS', type=int, default=0,
              help='The maximum duration to wait until the session starts.')
@click.option('--no-reuse', is_flag=True,
              help='Do not reuse existing sessions but return an error.')
# execution environment
@click.option('-e', '--env', metavar='KEY=VAL', type=str, multiple=True,
              help='Environment variable (may appear multiple times)')
# extra options
@click.option('--tag', type=str, default=None,
              help='User-defined tag string to annotate sessions.')
# resource spec
@click.option('-m', '--mount', type=str, multiple=True,
              help='User-owned virtual folder names to mount')
@click.option('--scaling-group', '--sgroup', type=str, default=None,
              help='The scaling group to execute session. If not specified, '
                   'all available scaling groups are included in the scheduling.')
@click.option('-r', '--resources', metavar='KEY=VAL', type=str, multiple=True,
              help='Set computation resources used by the session '
                   '(e.g: -r cpu=2 -r mem=256 -r gpu=1).'
                   '1 slot of cpu/gpu represents 1 core. '
                   'The unit of mem(ory) is MiB.')
@click.option('--cluster-size', metavar='NUMBER', type=int, default=1,
              help='The size of cluster in number of containers.')
@click.option('--resource-opts', metavar='KEY=VAL', type=str, multiple=True,
              help='Resource options for creating compute session '
                   '(e.g: shmem=64m)')
# resource grouping
@click.option('-d', '--domain', metavar='DOMAIN_NAME', default=None,
              help='Domain name where the session will be spawned. '
                   'If not specified, config\'s domain name will be used.')
@click.option('-g', '--group', metavar='GROUP_NAME', default=None,
              help='Group name where the session is spawned. '
                   'User should be a member of the group to execute the code.')
def start(image, session_id, owner,                                 # base args
          type, startup_command, enqueue_only, max_wait, no_reuse,  # job scheduling options
          env,                                            # execution environment
          tag,                                            # extra options
          mount, scaling_group, resources, cluster_size,  # resource spec
          resource_opts,
          domain, group):                                 # resource grouping
    '''
    Prepare and start a single compute session without executing codes.
    You may use the created session to execute codes using the "run" command
    or connect to an application service provided by the session using the "app"
    command.


    \b
    IMAGE: The name (and version/platform tags appended after a colon) of session
           runtime or programming language.
    '''
    if session_id is None:
        session_id = token_hex(5)
    else:
        session_id = session_id

    ######
    envs = _prepare_env_arg(env)
    resources = _prepare_resource_arg(resources)
    resource_opts = _prepare_resource_arg(resource_opts)
    mount = _prepare_mount_arg(mount)
    with Session() as session:
        try:
            kernel = session.Kernel.get_or_create(
                image,
                client_token=session_id,
                type_=type,
                enqueue_only=enqueue_only,
                max_wait=max_wait,
                no_reuse=no_reuse,
                cluster_size=cluster_size,
                mounts=mount,
                envs=envs,
                startup_command=startup_command,
                resources=resources,
                resource_opts=resource_opts,
                owner_access_key=owner,
                domain_name=domain,
                group_name=group,
                scaling_group=scaling_group,
                tag=tag)
        except Exception as e:
            print_error(e)
            sys.exit(1)
        else:
            if kernel.status == 'PENDING':
                print_info('Session ID {0} is enqueued for scheduling.'
                           .format(session_id))
            elif kernel.status == 'RUNNING':
                if kernel.created:
                    print_info('Session ID {0} is created and ready.'
                               .format(session_id))
                else:
                    print_info('Session ID {0} is already running and ready.'
                               .format(session_id))
                if kernel.service_ports:
                    print_info('This session provides the following app services: ' +
                               ', '.join(sport['name']
                                         for sport in kernel.service_ports))
            elif kernel.status == 'TERMINATED':
                print_warn('Session ID {0} is already terminated.\n'
                           'This may be an error in the kernel image.'
                           .format(session_id))
            elif kernel.status == 'TIMEOUT':
                print_info('Session ID {0} is still on the job queue.'
                           .format(session_id))
            elif kernel.status in ('ERROR', 'CANCELLED'):
                print_fail('Session ID {0} has an error during scheduling/startup or cancelled.'
                           .format(session_id))


@main.command(aliases=['rm', 'kill'])
@click.argument('sess_id_or_alias', metavar='SESSID', nargs=-1)
@click.option('-o', '--owner', '--owner-access-key', metavar='ACCESS_KEY',
              help='Specify the owner of the target session explicitly.')
@click.option('-s', '--stats', is_flag=True,
              help='Show resource usage statistics after termination')
def terminate(sess_id_or_alias, owner, stats):
    '''
    Terminate the given session.

    SESSID: session ID or its alias given when creating the session.
    '''
    print_wait('Terminating the session(s)...')
    with Session() as session:
        has_failure = False
        for sess in sess_id_or_alias:
            try:
                kernel = session.Kernel(sess, owner)
                ret = kernel.destroy()
            except BackendAPIError as e:
                print_error(e)
                if e.status == 404:
                    print_info(
                        'If you are an admin, use "-o" / "--owner" option '
                        'to terminate other user\'s session.')
                has_failure = True
            except Exception as e:
                print_error(e)
                has_failure = True
            if has_failure:
                sys.exit(1)
        else:
            print_done('Done.')
            if stats:
                stats = ret.get('stats', None) if ret else None
                if stats:
                    print(_format_stats(stats))
                else:
                    print('Statistics is not available.')


@main.command()
@click.argument('sess_id_or_alias', metavar='NAME')
@click.option('-o', '--owner', '--owner-access-key', 'owner_access_key', metavar='ACCESS_KEY',
              help='Specify the owner of the target session explicitly.')
@click.pass_context
def info(ctx, sess_id_or_alias, owner_access_key):
    '''
    Show detailed information for a running compute session.
    This is an alias of the "admin session <sess_id>" command.

    SESSID: session ID or its alias given when creating the session.
    '''
    ctx.forward(cli_admin_session)


@main.command()
@click.argument('sess_id_or_alias', metavar='SESSID')
@click.option('-o', '--owner', '--owner-access-key', 'owner_access_key', metavar='ACCESS_KEY',
              help='Specify the owner of the target session explicitly.')
def events(sess_id_or_alias, owner_access_key):
    '''
    Monitor the lifecycle events of a compute session.

    SESSID: session ID or its alias given when creating the session.
    '''

    async def _run_events():
        async with AsyncSession() as session:
            kernel = session.Kernel(sess_id_or_alias, owner_access_key)
            async with kernel.stream_events() as sse_response:
                async for ev in sse_response.fetch_events():
                    print(click.style(ev['event'], fg='cyan', bold=True), json.loads(ev['data']))

    try:
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(_run_events())
        finally:
            loop.stop()
    except Exception as e:
        print_error(e)
