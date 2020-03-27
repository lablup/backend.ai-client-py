import json
import os
import secrets
import tarfile
import tempfile
from typing import (
    Iterable, Union,
    AsyncGenerator,
    Mapping,
    Sequence, List,
)
from pathlib import Path

import aiohttp
from aiohttp import hdrs
from tqdm import tqdm

from .base import api_function
from ..compat import current_loop
from ..config import DEFAULT_CHUNK_SIZE
from ..exceptions import BackendClientError
from ..request import (
    Request, AttachedFile,
    WebSocketResponse,
    SSEResponse,
)
from ..utils import undefined, ProgressReportingReader
from ..versioning import get_naming

__all__ = (
    'ComputeSession',
)


def drop(d, dropval):
    newd = {}
    for k, v in d.items():
        if isinstance(v, Mapping) or isinstance(v, dict):
            newd[k] = drop(v, dropval)
        elif v != dropval:
            newd[k] = v
    return newd


class ComputeSession:
    '''
    Provides various interactions with compute sessions in Backend.AI.

    The term 'kernel' is now deprecated and we prefer 'compute sessions'.
    However, for historical reasons and to avoid confusion with client sessions, we
    keep the backward compatibility with the naming of this API function class.

    For multi-container sessions, all methods take effects to the master container
    only, except :func:`~ComputeSession.destroy` and :func:`~ComputeSession.restart` methods.
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
    async def get_task_logs(
        cls, task_id: str, *,
        chunk_size: int = 8192
    ) -> AsyncGenerator[bytes, None]:
        prefix = get_naming(cls.session.api_version, 'path')
        rqst = Request(cls.session, 'GET', f'/{prefix}/_/logs', params={
            'taskId': task_id,
        })
        async with rqst.fetch() as resp:
            while True:
                chunk = await resp.raw_response.content.read(chunk_size)
                if not chunk:
                    break
                yield chunk

    @api_function
    @classmethod
    async def get_or_create(cls, image: str, *,
                            name: str = None,
                            type_: str = 'interactive',
                            enqueue_only: bool = False,
                            max_wait: int = 0,
                            no_reuse: bool = False,
                            mounts: Iterable[str] = None,
                            mount_map: Mapping[str, str] = None,
                            envs: Mapping[str, str] = None,
                            startup_command: str = None,
                            resources: Mapping[str, int] = None,
                            resource_opts: Mapping[str, int] = None,
                            cluster_size: int = 1,
                            domain_name: str = None,
                            group_name: str = None,
                            bootstrap_script: str = None,
                            tag: str = None,
                            scaling_group: str = None,
                            owner_access_key: str = None,
                            preopen_ports: List[int] = None) -> 'ComputeSession':
        '''
        Get-or-creates a compute session.
        If *name* is ``None``, it creates a new compute session as long as
        the server has enough resources and your API key has remaining quota.
        If *name* is a valid string and there is an existing compute session
        with the same token and the same *image*, then it returns the :class:`ComputeSession`
        instance representing the existing session.

        :param image: The image name and tag for the compute session.
            Example: ``python:3.6-ubuntu``.
            Check out the full list of available images in your server using (TODO:
            new API).
        :param name: A client-side (user-defined) identifier to distinguish the session among currently
            running sessions.
            It may be used to seamlessly reuse the session already created.

            .. versionchanged:: 19.12.0

               Renamed from ``clientSessionToken``.
        :param type_: Either ``"interactive"`` (default) or ``"batch"``.

            .. versionadded:: 19.09.0
        :param enqueue_only: Just enqueue the session creation request and return immediately,
            without waiting for its startup. (default: ``false`` to preserve the legacy
            behavior)

            .. versionadded:: 19.09.0
        :param max_wait: The time to wait for session startup. If the cluster resource
            is being fully utilized, this waiting time can be arbitrarily long due to
            job queueing.  If the timeout reaches, the returned *status* field becomes
            ``"TIMEOUT"``.  Still in this case, the session may start in the future.

            .. versionadded:: 19.09.0
        :param no_reuse: Raises an explicit error if a session with the same *image* and
            the same *name* already exists instead of returning the information
            of it.

            .. versionadded:: 19.09.0
        :param mounts: The list of vfolder names that belongs to the currrent API
            access key.
        :param mount_map: Mapping which contains custom path to mount vfolder.
            Key and value of this map should be vfolder name and custom path.
            All custom mounts should be under /home/work.
            vFolders which has a dot(.) prefix in its name are not affected.
        :param envs: The environment variables which always bypasses the jail policy.
        :param resources: The resource specification. (TODO: details)
        :param cluster_size: The number of containers in this compute session.
            Must be at least 1.
        :param tag: An optional string to annotate extra information.
        :param owner: An optional access key that owns the created session. (Only
            available to administrators)

        :returns: The :class:`ComputeSession` instance.
        '''
        if name:
            assert 4 <= len(name) <= 64, \
                   'Client session token should be 4 to 64 characters long.'
        else:
            name = f'pysdk-{secrets.token_hex(5)}'
        if mounts is None:
            mounts = []
        if mount_map is None:
            mount_map = {}
        if resources is None:
            resources = {}
        if resource_opts is None:
            resource_opts = {}
        if domain_name is None:
            # Even if config.domain is None, it can be guessed in the manager by user information.
            domain_name = cls.session.config.domain
        if group_name is None:
            group_name = cls.session.config.group

        mounts.extend(cls.session.config.vfolder_mounts)
        prefix = get_naming(cls.session.api_version, 'path')
        rqst = Request(cls.session, 'POST', f'/{prefix}')
        params = {
            'tag': tag,
            get_naming(cls.session.api_version, 'name_arg'): name,
            'config': {
                'mounts': mounts,
                'environ': envs,
                'clusterSize': cluster_size,
                'resources': resources,
                'resource_opts': resource_opts,
                'scalingGroup': scaling_group,
            },
        }
        if cls.session.api_version >= (5, '20191215'):
            params['config'].update({
                'mount_map': mount_map,
                'preopen_ports': preopen_ports,
            })
            params.update({
                'bootstrap_script': bootstrap_script,
            })
        if cls.session.api_version >= (4, '20190615'):
            params.update({
                'owner_access_key': owner_access_key,
                'domain': domain_name,
                'group': group_name,
                'type': type_,
                'enqueueOnly': enqueue_only,
                'maxWaitSeconds': max_wait,
                'reuseIfExists': not no_reuse,
                'startupCommand': startup_command,
            })
        if cls.session.api_version > (4, '20181215'):
            params['image'] = image
        else:
            params['lang'] = image
        rqst.set_json(params)
        async with rqst.fetch() as resp:
            data = await resp.json()
            o = cls(name, owner_access_key)  # type: ignore
            o.created = data.get('created', True)     # True is for legacy
            o.status = data.get('status', 'RUNNING')
            o.service_ports = data.get('servicePorts', [])
            o.domain = domain_name
            o.group = group_name
            return o

    @api_function
    @classmethod
    async def create_from_template(cls, template_id: str, *,
                                   name: str = undefined,
                                   type_: str = undefined,
                                   enqueue_only: bool = undefined,
                                   max_wait: int = undefined,
                                   no_reuse: bool = undefined,
                                   image: str = undefined,
                                   mounts: Iterable[str] = undefined,
                                   mount_map: Mapping[str, str] = undefined,
                                   envs: Mapping[str, str] = undefined,
                                   startup_command: str = undefined,
                                   resources: Mapping[str, int] = undefined,
                                   resource_opts: Mapping[str, int] = undefined,
                                   cluster_size: int = undefined,
                                   domain_name: str = undefined,
                                   group_name: str = undefined,
                                   bootstrap_script: str = undefined,
                                   tag: str = undefined,
                                   scaling_group: str = undefined,
                                   owner_access_key: str = undefined) -> 'ComputeSession':
        '''
        Get-or-creates a compute session from template.
        All other parameters provided  will be overwritten to template, including
        vfolder mounts (not appended!).
        If *name* is ``None``, it creates a new compute session as long as
        the server has enough resources and your API key has remaining quota.
        If *name* is a valid string and there is an existing compute session
        with the same token and the same *image*, then it returns the :class:`ComputeSession`
        instance representing the existing session.

        :param template_id: Task template to apply to compute session.
        :param image: The image name and tag for the compute session.
            Example: ``python:3.6-ubuntu``.
            Check out the full list of available images in your server using (TODO:
            new API).
        :param name: A client-side (user-defined) identifier to distinguish the session among currently
            running sessions.
            It may be used to seamlessly reuse the session already created.

            .. versionchanged:: 19.12.0

               Renamed from ``clientSessionToken``.
        :param type_: Either ``"interactive"`` (default) or ``"batch"``.

            .. versionadded:: 19.09.0
        :param enqueue_only: Just enqueue the session creation request and return immediately,
            without waiting for its startup. (default: ``false`` to preserve the legacy
            behavior)

            .. versionadded:: 19.09.0
        :param max_wait: The time to wait for session startup. If the cluster resource
            is being fully utilized, this waiting time can be arbitrarily long due to
            job queueing.  If the timeout reaches, the returned *status* field becomes
            ``"TIMEOUT"``.  Still in this case, the session may start in the future.

            .. versionadded:: 19.09.0
        :param no_reuse: Raises an explicit error if a session with the same *image* and
            the same *name* already exists instead of returning the information
            of it.

            .. versionadded:: 19.09.0
        :param mounts: The list of vfolder names that belongs to the currrent API
            access key.
        :param mount_map: Mapping which contains custom path to mount vfolder.
            Key and value of this map should be vfolder name and custom path.
            All custom mounts should be under /home/work.
            vFolders which has a dot(.) prefix in its name are not affected.
        :param envs: The environment variables which always bypasses the jail policy.
        :param resources: The resource specification. (TODO: details)
        :param cluster_size: The number of containers in this compute session.
            Must be at least 1.
        :param tag: An optional string to annotate extra information.
        :param owner: An optional access key that owns the created session. (Only
            available to administrators)

        :returns: The :class:`ComputeSession` instance.
        '''
        if name:
            assert 4 <= len(name) <= 64, \
                   'Client session token should be 4 to 64 characters long.'
        else:
            name = f'pysdk-{secrets.token_urlsafe(8)}'

        if domain_name is None:
            # Even if config.domain is None, it can be guessed in the manager by user information.
            domain_name = cls.session.config.domain
        if group_name is None:
            group_name = cls.session.config.group
        if cls.session.config.vfolder_mounts:
            mounts.extend(cls.session.config.vfolder_mounts)
        prefix = get_naming(cls.session.api_version, 'path')
        rqst = Request(cls.session, 'POST', f'/{prefix}/_/create-from-template')
        params = {
            'template_id': template_id,
            'tag': tag,
            'image': image,
            'domain': domain_name,
            'group': group_name,
            get_naming(cls.session.api_version, 'name_arg'): name,
            'bootstrap_script': bootstrap_script,
            'enqueueOnly': enqueue_only,
            'maxWaitSeconds': max_wait,
            'reuseIfExists': not no_reuse,
            'startupCommand': startup_command,
            'owner_access_key': owner_access_key,
            'type': type_,
            'config': {
                'mounts': mounts,
                'mount_map': mount_map,
                'environ': envs,
                'clusterSize': cluster_size,
                'resources': resources,
                'resource_opts': resource_opts,
                'scalingGroup': scaling_group,
            },
        }
        params = drop(params, undefined)
        rqst.set_json(params)
        async with rqst.fetch() as resp:
            data = await resp.json()
            o = cls(name, owner_access_key)
            o.created = data.get('created', True)     # True is for legacy
            o.status = data.get('status', 'RUNNING')
            o.service_ports = data.get('servicePorts', [])
            o.domain = domain_name
            o.group = group_name
            return o

    def __init__(self, name: str, owner_access_key: str = None):
        self.name = name
        self.owner_access_key = owner_access_key

    @api_function
    async def destroy(self, *, forced: bool = False):
        '''
        Destroys the compute session.
        Since the server literally kills the container(s), all ongoing executions are
        forcibly interrupted.
        '''
        params = {}
        if self.owner_access_key:
            params['owner_access_key'] = self.owner_access_key
        prefix = get_naming(self.session.api_version, 'path')
        if forced:
            params['forced'] = 'true'
        rqst = Request(
            self.session,
            'DELETE', f'/{prefix}/{self.name}',
            params=params,
        )
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
        params = {}
        if self.owner_access_key:
            params['owner_access_key'] = self.owner_access_key
        prefix = get_naming(self.session.api_version, 'path')
        rqst = Request(
            self.session,
            'PATCH', f'/{prefix}/{self.name}',
            params=params,
        )
        async with rqst.fetch():
            pass

    @api_function
    async def interrupt(self):
        '''
        Tries to interrupt the current ongoing code execution.
        This may fail without any explicit errors depending on the code being
        executed.
        '''
        params = {}
        if self.owner_access_key:
            params['owner_access_key'] = self.owner_access_key
        prefix = get_naming(self.session.api_version, 'path')
        rqst = Request(
            self.session,
            'POST', f'/{prefix}/{self.name}/interrupt',
            params=params,
        )
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
        params = {}
        if self.owner_access_key:
            params['owner_access_key'] = self.owner_access_key
        prefix = get_naming(self.session.api_version, 'path')
        rqst = Request(
            self.session,
            'POST', f'/{prefix}/{self.name}/complete',
            params=params,
        )
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
        params = {}
        if self.owner_access_key:
            params['owner_access_key'] = self.owner_access_key
        prefix = get_naming(self.session.api_version, 'path')
        rqst = Request(
            self.session,
            'GET', f'/{prefix}/{self.name}',
            params=params,
        )
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    async def get_logs(self):
        '''
        Retrieves the console log of the compute session container.
        '''
        params = {}
        if self.owner_access_key:
            params['owner_access_key'] = self.owner_access_key
        prefix = get_naming(self.session.api_version, 'path')
        rqst = Request(
            self.session,
            'GET', f'/{prefix}/{self.name}/logs',
            params=params,
        )
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
        params = {}
        if self.owner_access_key:
            params['owner_access_key'] = self.owner_access_key
        prefix = get_naming(self.session.api_version, 'path')
        if mode in {'query', 'continue', 'input'}:
            assert code is not None, \
                   'The code argument must be a valid string even when empty.'
            rqst = Request(
                self.session,
                'POST', f'/{prefix}/{self.name}',
                params=params,
            )
            rqst.set_json({
                'mode': mode,
                'code': code,
                'runId': run_id,
            })
        elif mode == 'batch':
            rqst = Request(
                self.session,
                'POST', f'/{prefix}/{self.name}',
                params=params,
            )
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
            rqst = Request(
                self.session,
                'POST', f'/{prefix}/{self.name}',
                params=params,
            )
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
        params = {}
        if self.owner_access_key:
            params['owner_access_key'] = self.owner_access_key
        prefix = get_naming(self.session.api_version, 'path')
        base_path = (
            Path.cwd() if basedir is None
            else Path(basedir).resolve()
        )
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

            rqst = Request(
                self.session,
                'POST', f'/{prefix}/{self.name}/upload',
                params=params,
            )
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
        params = {}
        if self.owner_access_key:
            params['owner_access_key'] = self.owner_access_key
        prefix = get_naming(self.session.api_version, 'path')
        rqst = Request(
            self.session,
            'GET', f'/{prefix}/{self.name}/download',
            params=params,
        )
        rqst.set_json({
            'files': [*map(str, files)],
        })
        file_names = []
        async with rqst.fetch() as resp:
            loop = current_loop()
            tqdm_obj = tqdm(desc='Downloading files',
                            unit='bytes', unit_scale=True,
                            total=resp.content.total_bytes,
                            disable=not show_progress)
            reader = aiohttp.MultipartReader.from_response(resp.raw_response)
            with tqdm_obj as pbar:
                while True:
                    part = await reader.next()
                    if part is None:
                        break
                    assert part.headers.get(hdrs.CONTENT_ENCODING, 'identity').lower() == 'identity'
                    assert part.headers.get(hdrs.CONTENT_TRANSFER_ENCODING, 'binary').lower() in (
                        'binary', '8bit', '7bit',
                    )
                    fp = tempfile.NamedTemporaryFile(suffix='.tar',
                                                     delete=False)
                    while True:
                        chunk = await part.read_chunk(DEFAULT_CHUNK_SIZE)
                        if not chunk:
                            break
                        await loop.run_in_executor(None, lambda: fp.write(chunk))
                        pbar.update(len(chunk))
                    fp.close()
                    with tarfile.open(fp.name) as tarf:
                        tarf.extractall(path=dest)
                        file_names.extend(tarf.getnames())
                    os.unlink(fp.name)
        return {'file_names': file_names}

    @api_function
    async def list_files(self, path: Union[str, Path] = '.'):
        '''
        Gets the list of files in the given path inside the compute session
        container.

        :param path: The directory path in the compute session.
        '''
        params = {}
        if self.owner_access_key:
            params['owner_access_key'] = self.owner_access_key
        prefix = get_naming(self.session.api_version, 'path')
        rqst = Request(
            self.session,
            'GET', f'/{prefix}/{self.name}/files',
            params=params,
        )
        rqst.set_json({
            'path': path,
        })
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    async def stream_app_info(self):
        params = {}
        if self.owner_access_key:
            params['owner_access_key'] = self.owner_access_key
        prefix = get_naming(self.session.api_version, 'path')
        api_rqst = Request(
            self.session,
            'GET', f'/stream/{prefix}/{self.name}/apps',
            params=params,
        )
        async with api_rqst.fetch() as resp:
            return await resp.json()

    # only supported in AsyncKernel
    def stream_events(self) -> SSEResponse:
        '''
        Opens the stream of the kernel lifecycle events.
        Only the master kernel of each session is monitored.

        :returns: a :class:`StreamEvents` object.
        '''
        params = {
            get_naming(self.session.api_version, 'event_name_arg'): self.name,
        }
        if self.owner_access_key:
            params['owner_access_key'] = self.owner_access_key
        prefix = get_naming(self.session.api_version, 'path')
        request = Request(
            self.session,
            'GET', f'/stream/{prefix}/_/events',
            params=params,
        )
        return request.connect_events()

    # only supported in AsyncKernel
    def stream_pty(self) -> 'StreamPty':
        '''
        Opens a pseudo-terminal of the kernel (if supported) streamed via
        websockets.

        :returns: a :class:`StreamPty` object.
        '''
        params = {}
        if self.owner_access_key:
            params['owner_access_key'] = self.owner_access_key
        prefix = get_naming(self.session.api_version, 'path')
        request = Request(
            self.session,
            'GET', f'/stream/{prefix}/{self.name}/pty',
            params=params,
        )
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
        params = {}
        if self.owner_access_key:
            params['owner_access_key'] = self.owner_access_key
        prefix = get_naming(self.session.api_version, 'path')
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
        request = Request(
            self.session,
            'GET', f'/stream/{prefix}/{self.name}/execute',
            params=params,
        )

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
