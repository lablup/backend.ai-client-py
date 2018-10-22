import json
import os
import tarfile
import tempfile
from typing import Iterable, Mapping, Sequence, Union
from pathlib import Path
import uuid

import aiohttp.web
from tqdm import tqdm

from .base import BaseFunction, SyncFunctionMixin
from .exceptions import BackendClientError
from .request import Request
from .cli.pretty import ProgressReportingReader

__all__ = (
    'BaseKernel',
    'Kernel',
)


class BaseKernel(BaseFunction):

    '''
    Implements the request creation and response handling logic,
    while delegating the process of request sending to the subclasses
    via the generator protocol.
    '''

    _session = None

    @classmethod
    def _get_or_create(cls, lang: str,
                       client_token: str=None,
                       mounts: Iterable[str]=None,
                       envs: Mapping[str, str]=None,
                       resources: Mapping[str, int]=None,
                       max_mem: int=0, exec_timeout: int=0) -> str:
        if client_token:
            assert 4 <= len(client_token) <= 64, \
                   'Client session token should be 4 to 64 characters long.'
        else:
            client_token = uuid.uuid4().hex
        if mounts is None:
            mounts = []
        if resources is None:
            resources = {}
        mounts.extend(cls._session.config.vfolder_mounts)
        resp = yield Request(cls._session, 'POST', '/kernel/create', {
            'lang': lang,
            'clientSessionToken': client_token,
            'config': {
                'mounts': mounts,
                'environ': envs,
                'instanceMemory': resources.get('ram'),
                'instanceCores': resources.get('cpu'),
                'instanceGPUs': resources.get('gpu'),
            },
        })
        data = resp.json()
        o = cls(data['kernelId'])  # type: ignore
        o.created = data.get('created', True)     # True is for legacy
        return o

    def _destroy(self):
        resp = yield Request(self._session,
                             'DELETE', '/kernel/{}'.format(self.kernel_id))
        if resp.status == 200:
            return resp.json()

    def _restart(self):
        yield Request(self._session,
                      'PATCH', '/kernel/{}'.format(self.kernel_id))

    def _interrupt(self):
        yield Request(self._session,
                      'POST', '/kernel/{}/interrupt'.format(self.kernel_id))

    def _complete(self, code: str, opts: dict=None):
        opts = {} if opts is None else opts
        rqst = Request(self._session,
            'POST', '/kernel/{}/complete'.format(self.kernel_id), {
                'code': code,
                'options': {
                    'row': int(opts.get('row', 0)),
                    'col': int(opts.get('col', 0)),
                    'line': opts.get('line', ''),
                    'post': opts.get('post', ''),
                },
            })
        resp = yield rqst
        return resp.json()

    def _get_info(self):
        resp = yield Request(self._session,
                             'GET', '/kernel/{}'.format(self.kernel_id))
        return resp.json()

    def _get_logs(self):
        resp = yield Request(self._session,
                             'GET', '/kernel/{}/logs'.format(self.kernel_id))
        return resp.json()

    def _execute(self, run_id: str=None,
                 code: str=None,
                 mode: str='query',
                 opts: dict=None):
        opts = {} if opts is None else opts
        if mode in {'query', 'continue', 'input'}:
            assert code is not None  # but maybe empty due to continuation
            rqst = Request(self._session,
                'POST', '/kernel/{}'.format(self.kernel_id), {
                    'mode': mode,
                    'code': code,
                    'runId': run_id,
                })
        elif mode == 'batch':
            rqst = Request(self._session,
                'POST', '/kernel/{}'.format(self.kernel_id), {
                    'mode': mode,
                    'code': code,
                    'runId': run_id,
                    'options': {
                        'clean': opts.get('clean', None),
                        'build': opts.get('build', None),
                        'buildLog': bool(opts.get('buildLog', False)),
                        'exec': opts.get('exec', None),
                    },
                })
        elif mode == 'complete':
            rqst = Request(self._session,
                'POST', '/kernel/{}/complete'.format(self.kernel_id), {
                    'code': code,
                    'options': {
                        'row': int(opts.get('row', 0)),
                        'col': int(opts.get('col', 0)),
                        'line': opts.get('line', ''),
                        'post': opts.get('post', ''),
                    },
                })
        else:
            raise BackendClientError('Invalid execution mode: {0}'.format(mode))
        resp = yield rqst
        return resp.json()['result']

    def _upload(self, files: Sequence[Union[str, Path]],
               basedir: Union[str, Path]=None,
               show_progress: bool=False):
        fields = []
        base_path = (Path.cwd() if basedir is None
                     else Path(basedir).resolve())
        files = [Path(file).resolve() for file in files]
        total_size = 0
        for file_path in files:
            total_size += file_path.stat().st_size
        tqdm_obj = tqdm(desc='Uploading files',
                        unit='bytes', unit_scale=True,
                        total=total_size,
                        disable=not show_progress)
        with tqdm_obj:
            for file_path in files:
                try:
                    fields.append(aiohttp.web.FileField(
                        'src',
                        str(file_path.relative_to(base_path)),
                        ProgressReportingReader(str(file_path),
                                                tqdm_instance=tqdm_obj),
                        'application/octet-stream',
                        None
                    ))
                except ValueError:
                    msg = 'File "{0}" is outside of the base directory "{1}".' \
                          .format(file_path, base_path)
                    raise ValueError(msg) from None

            rqst = Request(self._session,
                           'POST', '/kernel/{}/upload'.format(self.kernel_id))
            rqst.content = fields
            resp = yield rqst
        return resp

    def _download(self, files: Sequence[Union[str, Path]],
                  show_progress: bool=False):
        resp = yield Request(self._session,
            'GET', '/kernel/{}/download'.format(self.kernel_id), {
                'files': files,
            })
        chunk_size = 1 * 1024
        tqdm_obj = tqdm(desc='Downloading files',
                        unit='bytes', unit_scale=True,
                        total=resp.stream_reader.total_bytes,
                        disable=not show_progress)
        with tqdm_obj as pbar:
            fp = None
            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                pbar.update(len(chunk))
                # TODO: more elegant parsing of multipart response?
                for part in chunk.split(b'\r\n'):
                    if part.startswith(b'--'):
                        if fp:
                            fp.close()
                            with tarfile.open(fp.name) as tarf:
                                tarf.extractall()
                            os.unlink(fp.name)
                        fp = tempfile.NamedTemporaryFile(suffix='.tar', delete=False)
                    elif part.startswith(b'Content-') or part == b'':
                        continue
                    else:
                        fp.write(part)
            if fp:
                fp.close()
                os.unlink(fp.name)
        return resp

    def _list_files(self, path: Union[str, Path]='.'):
        resp = yield Request(self._session,
            'GET', '/kernel/{}/files'.format(self.kernel_id), {
                'path': path,
            })
        return resp.json()

    # only supported in AsyncKernel
    async def stream_pty(self):
        request = Request(self._session,
                          'GET', '/stream/kernel/{}/pty'.format(self.kernel_id))
        try:
            ws = await request.connect_websocket()
        except aiohttp.ClientResponseError as e:
            raise BackendClientError(e.code, e.message)
        return StreamPty(self.kernel_id, ws)

    def __init__(self, kernel_id: str) -> None:
        self.kernel_id = kernel_id
        self.destroy   = self._call_base_method(self._destroy)
        self.restart   = self._call_base_method(self._restart)
        self.interrupt = self._call_base_method(self._interrupt)
        self.complete  = self._call_base_method(self._complete)
        self.get_info  = self._call_base_method(self._get_info)
        self.get_logs  = self._call_base_method(self._get_logs)
        self.execute   = self._call_base_method(self._execute)
        self.upload    = self._call_base_method(self._upload)
        self.download  = self._call_base_method(self._download)
        self.list_files = self._call_base_method(self._list_files)

    def __init_subclass__(cls):
        cls.get_or_create = cls._call_base_clsmethod(cls._get_or_create)


class Kernel(SyncFunctionMixin, BaseKernel):
    '''
    Deprecated! Use ai.backend.client.Session instead.
    '''
    pass


class StreamPty:

    '''
    A very thin wrapper of aiohttp.WebSocketResponse object.
    It keeps the reference to the mother aiohttp.ClientSession object while the
    connection is alive.
    '''

    def __init__(self, kernel_id, ws):
        self.kernel_id = kernel_id
        self.ws = ws

    @property
    def closed(self):
        return self.ws.closed

    def __aiter__(self):
        return self.ws.__aiter__()

    async def __anext__(self):
        msg = await self.ws.__anext__()
        return msg

    def exception(self):
        return self.ws.exception()

    async def send_str(self, raw_str):
        await self.ws.send_str(raw_str)

    async def resize(self, rows, cols):
        await self.ws.send_str(json.dumps({
            'type': 'resize',
            'rows': rows,
            'cols': cols,
        }))

    async def restart(self):
        await self.ws.send_str(json.dumps({
            'type': 'restart',
        }))

    async def close(self):
        await self.ws.close()
