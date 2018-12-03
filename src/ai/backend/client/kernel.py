import json
import os
import tarfile
import tempfile
from typing import Iterable, Mapping, Sequence, Union
from pathlib import Path
import uuid

from tqdm import tqdm

from .base import api_function
from .exceptions import BackendClientError
from .request import (
    Request, AttachedFile,
    WebSocketResponse
)
from .cli.pretty import ProgressReportingReader

__all__ = (
    'Kernel',
)


class Kernel:

    '''
    Implements the request creation and response handling logic,
    while delegating the process of request sending to the subclasses
    via the generator protocol.
    '''

    session = None

    @api_function
    @classmethod
    async def get_or_create(cls, lang: str, *,
                            client_token: str = None,
                            mounts: Iterable[str] = None,
                            envs: Mapping[str, str] = None,
                            resources: Mapping[str, int] = None,
                            cluster_size: int = 1,
                            exec_timeout: int = 0,
                            tag: str = None) -> 'Kernel':
        if client_token:
            assert 4 <= len(client_token) <= 64, \
                   'Client session token should be 4 to 64 characters long.'
        else:
            client_token = uuid.uuid4().hex
        if mounts is None:
            mounts = []
        if resources is None:
            resources = {}
        mounts.extend(cls.session.config.vfolder_mounts)
        rqst = Request(cls.session, 'POST', '/kernel/create')
        rqst.set_json({
            'lang': lang,
            'tag': tag,
            'clientSessionToken': client_token,
            'config': {
                'mounts': mounts,
                'environ': envs,
                'clusterSize': cluster_size,
                'instanceMemory': (resources.get('mem', None) or
                                   resources.get('ram', None)),  # legacy
                'instanceCores': resources.get('cpu', None),
                'instanceGPUs': resources.get('gpu', None),
                'instanceTPUs': resources.get('tpu', None),
            },
        })
        async with rqst.fetch() as resp:
            data = await resp.json()
            o = cls(data['kernelId'])  # type: ignore
            o.created = data.get('created', True)     # True is for legacy
            return o

    def __init__(self, kernel_id: str):
        self.kernel_id = kernel_id

    @api_function
    async def destroy(self):
        rqst = Request(self.session,
                       'DELETE', '/kernel/{}'.format(self.kernel_id))
        async with rqst.fetch() as resp:
            if resp.status == 200:
                return await resp.json()

    @api_function
    async def restart(self):
        rqst = Request(self.session,
                       'PATCH', '/kernel/{}'.format(self.kernel_id))
        async with rqst.fetch():
            pass

    @api_function
    async def interrupt(self):
        rqst = Request(self.session,
                       'POST', '/kernel/{}/interrupt'.format(self.kernel_id))
        async with rqst.fetch():
            pass

    @api_function
    async def complete(self, code: str, opts: dict = None):
        opts = {} if opts is None else opts
        rqst = Request(self.session,
            'POST', '/kernel/{}/complete'.format(self.kernel_id))
        rqst.set_json({
            'code': code,
            'options': {
                'row': int(opts.get('row', 0)),
                'col': int(opts.get('col', 0)),
                'line': opts.get('line', ''),
                'post': opts.get('post', ''),
            },
        })
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    async def get_info(self):
        rqst = Request(self.session,
                       'GET', '/kernel/{}'.format(self.kernel_id))
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    async def get_logs(self):
        rqst = Request(self.session,
                       'GET', '/kernel/{}/logs'.format(self.kernel_id))
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    async def execute(self, run_id: str = None,
                      code: str = None,
                      mode: str = 'query',
                      opts: dict = None):
        opts = opts if opts is not None else {}
        if mode in {'query', 'continue', 'input'}:
            assert code is not None  # but maybe empty due to continuation
            rqst = Request(self.session,
                'POST', '/kernel/{}'.format(self.kernel_id))
            rqst.set_json({
                'mode': mode,
                'code': code,
                'runId': run_id,
            })
        elif mode == 'batch':
            rqst = Request(self.session,
                'POST', '/kernel/{}'.format(self.kernel_id))
            rqst.set_json({
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
            rqst = Request(self.session,
                'POST', '/kernel/{}/complete'.format(self.kernel_id))
            rqst.set_json({
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
        async with rqst.fetch() as resp:
            return (await resp.json())['result']

    @api_function
    async def upload(self, files: Sequence[Union[str, Path]],
                     basedir: Union[str, Path] = None,
                     show_progress: bool = False):
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
            attachments = []
            for file_path in files:
                try:
                    attachments.append(AttachedFile(
                        str(file_path.relative_to(base_path)),
                        ProgressReportingReader(str(file_path),
                                                tqdm_instance=tqdm_obj),
                        'application/octet-stream',
                    ))
                except ValueError:
                    msg = 'File "{0}" is outside of the base directory "{1}".' \
                          .format(file_path, base_path)
                    raise ValueError(msg) from None

            rqst = Request(self.session,
                           'POST', '/kernel/{}/upload'.format(self.kernel_id))
            rqst.attach_files(attachments)
            async with rqst.fetch() as resp:
                return resp

    @api_function
    async def download(self, files: Sequence[Union[str, Path]],
                       dest: Union[str, Path] = '.',
                       show_progress: bool = False):
        rqst = Request(self.session,
                       'GET', '/kernel/{}/download'.format(self.kernel_id))
        rqst.set_json({
            'files': files,
        })
        async with rqst.fetch() as resp:
            chunk_size = 1 * 1024
            file_names = None
            tqdm_obj = tqdm(desc='Downloading files',
                            unit='bytes', unit_scale=True,
                            total=resp.content.total_bytes,
                            disable=not show_progress)
            with tqdm_obj as pbar:
                fp = None
                while True:
                    chunk = await resp.aread(chunk_size)
                    if not chunk:
                        break
                    pbar.update(len(chunk))
                    # TODO: more elegant parsing of multipart response?
                    for part in chunk.split(b'\r\n'):
                        if part.startswith(b'--'):
                            if fp:
                                fp.close()
                                with tarfile.open(fp.name) as tarf:
                                    tarf.extractall(path=dest)
                                    file_names = tarf.getnames()
                                os.unlink(fp.name)
                            fp = tempfile.NamedTemporaryFile(suffix='.tar',
                                                             delete=False)
                        elif part.startswith(b'Content-') or part == b'':
                            continue
                        else:
                            fp.write(part)
                if fp:
                    fp.close()
                    os.unlink(fp.name)
            result = {'file_names': file_names}
            return result

    @api_function
    async def list_files(self, path: Union[str, Path] = '.'):
        rqst = Request(self.session,
                       'GET', '/kernel/{}/files'.format(self.kernel_id))
        rqst.set_json({
            'path': path,
        })
        async with rqst.fetch() as resp:
            return await resp.json()

    # only supported in AsyncKernel
    def stream_pty(self):
        request = Request(self.session,
                          'GET', '/stream/kernel/{}/pty'.format(self.kernel_id))
        return request.connect_websocket(response_cls=StreamPty)

    # only supported in AsyncKernel
    def stream_execute(self, code: str = '', *,
                       mode: str = 'query',
                       opts: dict = None):
        opts = {} if opts is None else opts
        if mode == 'query':
            opts = {}
        elif mode == 'batch':
            opts = {
                'clean': opts.get('clean', None),
                'build': opts.get('build', None),
                'buildLog': bool(opts.get('buildLog', False)),
                'exec': opts.get('exec', None),
            }
        else:
            msg = 'Invalid stream-execution mode: {0}'.format(mode)
            raise BackendClientError(msg)
        request = Request(self.session,
                          'GET', '/stream/kernel/{}/execute'.format(self.kernel_id))

        async def send_code(ws):
            await ws.send_json({
                'code': code,
                'mode': mode,
                'options': opts,
            })

        return request.connect_websocket(on_enter=send_code)


class StreamPty(WebSocketResponse):

    __slots__ = ('ws', )

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
