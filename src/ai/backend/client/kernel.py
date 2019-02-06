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
    Provides various interactions with compute sessions in Backend.AI.

    The term 'kernel' is now deprecated and we prefer 'compute sessions'.
    However, for historical reasons and to avoid confusion with client sessions, we
    keep the backward compatibility with the naming of this API function class.

    For multi-container sessions, all methods take effects to the master container
    only, except :func:`~Kernel.destroy` and :func:`~Kernel.restart` methods.
    So it is the user's responsibility to distribute uploaded files to multiple
    containers using explicit copies or virtual folders which are commonly mounted to
    all containers belonging to the same compute session.
    '''

    session = None
    '''The client session instance that this function class is bound to.'''

    @api_function
    @classmethod
    async def hello(cls) -> str:
        rqst = Request(cls.session, 'GET', '/')
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def get_or_create(cls, lang: str, *,
                            client_token: str = None,
                            mounts: Iterable[str] = None,
                            envs: Mapping[str, str] = None,
                            resources: Mapping[str, int] = None,
                            cluster_size: int = 1,
                            tag: str = None) -> 'Kernel':
        '''
        Get-or-creates a compute session.
        If *client_token* is ``None``, it creates a new compute session as long as
        the server has enough resources and your API key has remaining quota.
        If *client_token* is a valid string and there is an existing compute session
        with the same token and the same *lang*, then it returns the :class:`Kernel`
        instance representing the existing session.

        :param lang: The image name and tag for the compute session.
            Example: ``python:3.6-ubuntu``.
            Check out the full list of available images in your server using (TODO:
            new API).
        :param client_token: A client-side identifier to seamlessly reuse the compute
            session already created.
        :param mounts: The list of vfolder names that belongs to the currrent API
            access key.
        :param envs: The environment variables which always bypasses the jail policy.
        :param resources: The resource specification. (TODO: details)
        :param cluster_size: The number of containers in this compute session.
            Must be at least 1.
        :param tag: An optional string to annotate extra information.

        :returns: The :class:`Kernel` instance.
        '''
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
                'resources': resources,
            },
        })
        async with rqst.fetch() as resp:
            data = await resp.json()
            o = cls(data['kernelId'])  # type: ignore
            o.created = data.get('created', True)     # True is for legacy
            o.service_ports = data.get('servicePorts', [])
            return o

    def __init__(self, kernel_id: str):
        self.kernel_id = kernel_id

    @api_function
    async def destroy(self):
        '''
        Destroys the compute session.
        Since the server literally kills the container(s), all ongoing executions are
        forcibly interrupted.
        '''
        rqst = Request(self.session,
                       'DELETE', '/kernel/{}'.format(self.kernel_id))
        async with rqst.fetch() as resp:
            if resp.status == 200:
                return await resp.json()

    @api_function
    async def restart(self):
        '''
        Restarts the compute session.
        The server force-destroys the current running container(s), but keeps their
        temporary scratch directories intact.
        '''
        rqst = Request(self.session,
                       'PATCH', '/kernel/{}'.format(self.kernel_id))
        async with rqst.fetch():
            pass

    @api_function
    async def interrupt(self):
        '''
        Tries to interrupt the current ongoing code execution.
        This may fail without any explicit errors depending on the code being
        executed.
        '''
        rqst = Request(self.session,
                       'POST', '/kernel/{}/interrupt'.format(self.kernel_id))
        async with rqst.fetch():
            pass

    @api_function
    async def complete(self, code: str, opts: dict = None) -> Iterable[str]:
        '''
        Gets the auto-completion candidates from the given code string,
        as if a user has pressed the tab key just after the code in
        IDEs.

        Depending on the language of the compute session, this feature
        may not be supported.  Unsupported sessions returns an empty list.

        :param code: An (incomplete) code text.
        :param opts: Additional information about the current cursor position,
            such as row, col, line and the remainder text.

        :returns: An ordered list of strings.
        '''
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
        '''
        Retrieves a brief information about the compute session.
        '''
        rqst = Request(self.session,
                       'GET', '/kernel/{}'.format(self.kernel_id))
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    async def get_logs(self):
        '''
        Retrieves the console log of the compute session container.
        '''
        rqst = Request(self.session,
                       'GET', '/kernel/{}/logs'.format(self.kernel_id))
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    async def execute(self, run_id: str = None,
                      code: str = None,
                      mode: str = 'query',
                      opts: dict = None):
        '''
        Executes a code snippet directly in the compute session or sends a set of
        build/clean/execute commands to the compute session.

        For more details about using this API, please refer :doc:`the official API
        documentation <user-api/intro>`.

        :param run_id: A unique identifier for a particular run loop.  In the
            first call, it may be ``None`` so that the server auto-assigns one.
            Subsequent calls must use the returned ``runId`` value to request
            continuation or to send user inputs.
        :param code: A code snippet as string.  In the continuation requests, it
            must be an empty string.  When sending user inputs, this is where the
            user input string is stored.
        :param mode: A constant string which is one of ``"query"``, ``"batch"``,
            ``"continue"``, and ``"user-input"``.
        :param opts: A dict for specifying additional options. Mainly used in the
            batch mode to specify build/clean/execution commands.
            See :ref:`the API object reference <batch-execution-query-object>`
            for details.

        :returns: :ref:`An execution result object <execution-result-object>`
        '''
        opts = opts if opts is not None else {}
        if mode in {'query', 'continue', 'input'}:
            assert code is not None, \
                   'The code argument must be a valid string even when empty.'
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
        '''
        Uploads the given list of files to the compute session.
        You may refer them in the batch-mode execution or from the code
        executed in the server afterwards.

        :param files: The list of file paths in the client-side.
            If the paths include directories, the location of them in the compute
            session is calculated from the relative path to *basedir* and all
            intermediate parent directories are automatically created if not exists.

            For example, if a file path is ``/home/user/test/data.txt`` (or
            ``test/data.txt``) where *basedir* is ``/home/user`` (or the current
            working directory is ``/home/user``), the uploaded file is located at
            ``/home/work/test/data.txt`` in the compute session container.
        :param basedir: The directory prefix where the files reside.
            The default value is the current working directory.
        :param show_progress: Displays a progress bar during uploads.
        '''
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
        '''
        Downloads the given list of files from the compute session.

        :param files: The list of file paths in the compute session.
            If they are relative paths, the path is calculated from
            ``/home/work`` in the compute session container.
        :param dest: The destination directory in the client-side.
        :param show_progress: Displays a progress bar during downloads.
        '''
        rqst = Request(self.session,
                       'GET', '/kernel/{}/download'.format(self.kernel_id))
        rqst.set_json({
            'files': [*map(str, files)],
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
        '''
        Gets the list of files in the given path inside the compute session
        container.

        :param path: The directory path in the compute session.
        '''
        rqst = Request(self.session,
                       'GET', '/kernel/{}/files'.format(self.kernel_id))
        rqst.set_json({
            'path': path,
        })
        async with rqst.fetch() as resp:
            return await resp.json()

    # only supported in AsyncKernel
    def stream_pty(self) -> 'StreamPty':
        '''
        Opens a pseudo-terminal of the kernel (if supported) streamed via
        websockets.

        :returns: a :class:`StreamPty` object.
        '''
        request = Request(self.session,
                          'GET', '/stream/kernel/{}/pty'.format(self.kernel_id))
        return request.connect_websocket(response_cls=StreamPty)

    # only supported in AsyncKernel
    def stream_execute(self, code: str = '', *,
                       mode: str = 'query',
                       opts: dict = None) -> WebSocketResponse:
        '''
        Executes a code snippet in the streaming mode.
        Since the returned websocket represents a run loop, there is no need to
        specify *run_id* explicitly.
        '''
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
    '''
    A derivative class of :class:`~ai.backend.client.request.WebSocketResponse` which
    provides additional functions to control the terminal.
    '''

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
