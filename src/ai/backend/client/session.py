import abc
import asyncio
from contextvars import ContextVar, copy_context
import threading
from typing import (
    Any,
    Tuple,
)
import queue
import warnings

import aiohttp
from multidict import CIMultiDict

from .config import APIConfig, get_config, parse_api_version
from .exceptions import APIVersionWarning


__all__ = (
    'BaseSession',
    'Session',
    'AsyncSession',
    'api_session',
)


api_session: ContextVar['BaseSession'] = ContextVar('api_session', default=None)


def is_legacy_server():
    """
    Determine execution mode.

    Legacy mode: <= v4.20181215
    """
    with Session() as session:
        ret = session.ComputeSession.hello()
    bai_version = ret['version']
    legacy = True if bai_version <= 'v4.20181215' else False
    return legacy


async def _negotiate_api_version(
    http_session: aiohttp.ClientSession,
    config: APIConfig,
) -> Tuple[int, str]:
    client_version = parse_api_version(config.version)
    try:
        timeout_config = aiohttp.ClientTimeout(
            total=None, connect=None,
            sock_connect=config.connection_timeout,
            sock_read=config.read_timeout,
        )
        headers = CIMultiDict([
            ('User-Agent', config.user_agent),
        ])
        probe_url = config.endpoint / 'func/' if config.endpoint_type == 'session' else config.endpoint
        async with http_session.get(probe_url, timeout=timeout_config, headers=headers) as resp:
            resp.raise_for_status()
            server_info = await resp.json()
            server_version = parse_api_version(server_info['version'])
            if server_version > client_version:
                warnings.warn(
                    'The server API version is higher than the client. '
                    'Please upgrade the client package.',
                    category=APIVersionWarning,
                )
            return min(server_version, client_version)
    except (asyncio.TimeoutError, aiohttp.ClientError):
        # fallback to the configured API version
        return client_version


async def _close_aiohttp_session(session: aiohttp.ClientSession):
    # This is a hacky workaround for premature closing of SSL transports
    # on Windows Proactor event loops.
    # Thanks to Vadim Markovtsev's comment on the aiohttp issue #1925.
    # (https://github.com/aio-libs/aiohttp/issues/1925#issuecomment-592596034)
    transports = 0
    all_is_lost = asyncio.Event()
    if len(session.connector._conns) == 0:
        all_is_lost.set()
    for conn in session.connector._conns.values():
        for handler, _ in conn:
            proto = getattr(handler.transport, "_ssl_protocol", None)
            if proto is None:
                continue
            transports += 1
            orig_lost = proto.connection_lost
            orig_eof_received = proto.eof_received

            def connection_lost(exc):
                orig_lost(exc)
                nonlocal transports
                transports -= 1
                if transports == 0:
                    all_is_lost.set()

            def eof_received():
                try:
                    orig_eof_received()
                except AttributeError:
                    # It may happen that eof_received() is called after
                    # _app_protocol and _transport are set to None.
                    pass

            proto.connection_lost = connection_lost
            proto.eof_received = eof_received
    await session.close()
    if transports > 0:
        await all_is_lost.wait()


class _SyncWorkerThread(threading.Thread):

    sentinel = object()

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.work_queue = queue.Queue()
        self.done_queue = queue.Queue()

    def run(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            while True:
                item = self.work_queue.get()
                if item is self.sentinel:
                    break
                coro, ctx = item
                try:
                    result = ctx.run(loop.run_until_complete, coro)
                except Exception as e:
                    self.done_queue.put_nowait(e)
                else:
                    self.done_queue.put_nowait(result)
                self.work_queue.task_done()
        except (SystemExit, KeyboardInterrupt):
            pass
        finally:
            loop.stop()

    def execute(self, coro) -> Any:
        ctx = copy_context()  # preserve context for another thread
        try:
            self.work_queue.put((coro, ctx))
            result = self.done_queue.get()
            self.done_queue.task_done()
            if isinstance(result, Exception):
                raise result
            return result
        finally:
            del ctx


class BaseSession(metaclass=abc.ABCMeta):
    """
    The base abstract class for sessions.
    """

    __slots__ = (
        '_config', '_closed', 'aiohttp_session',
        '_context_token',
        'api_version',
        'System', 'Manager', 'Admin',
        'Agent', 'AgentWatcher', 'ScalingGroup',
        'Image', 'ComputeSession', 'SessionTemplate',
        'Domain', 'Group', 'Auth', 'User', 'KeyPair',
        'BackgroundTask',
        'EtcdConfig',
        'Resource', 'KeypairResourcePolicy',
        'VFolder', 'Dotfile'
    )

    aiohttp_session: aiohttp.ClientSession
    api_version: Tuple[int, str]

    def __init__(self, *, config: APIConfig = None):
        self._closed = False
        self._config = config if config else get_config()

        from .func.system import System
        from .func.admin import Admin
        from .func.agent import Agent, AgentWatcher
        from .func.auth import Auth
        from .func.bgtask import BackgroundTask
        from .func.domain import Domain
        from .func.etcd import EtcdConfig
        from .func.group import Group
        from .func.image import Image
        from .func.session import ComputeSession
        from .func.keypair import KeyPair
        from .func.manager import Manager
        from .func.resource import Resource
        from .func.keypair_resource_policy import KeypairResourcePolicy
        from .func.scaling_group import ScalingGroup
        from .func.session_template import SessionTemplate
        from .func.user import User
        from .func.vfolder import VFolder
        from .func.dotfile import Dotfile

        self.System = System
        self.Admin = Admin
        self.Agent = Agent
        self.AgentWatcher = AgentWatcher
        self.Auth = Auth
        self.BackgroundTask = BackgroundTask
        self.EtcdConfig = EtcdConfig
        self.Domain = Domain
        self.Group = Group
        self.Image = Image
        self.ComputeSession = ComputeSession
        self.KeyPair = KeyPair
        self.Manager = Manager
        self.Resource = Resource
        self.KeypairResourcePolicy = KeypairResourcePolicy
        self.User = User
        self.ScalingGroup = ScalingGroup
        self.SessionTemplate = SessionTemplate
        self.VFolder = VFolder
        self.Dotfile = Dotfile

    @abc.abstractmethod
    def close(self):
        """
        Terminates the session and releases underlying resources.
        """
        raise NotImplementedError

    @property
    def closed(self) -> bool:
        """
        Checks if the session is closed.
        """
        return self._closed

    @property
    def config(self):
        """
        The configuration used by this session object.
        """
        return self._config


class Session(BaseSession):
    """
    An API client session that makes API requests synchronously.
    You may call (almost) all function proxy methods like a plain Python function.
    It provides a context manager interface to ensure closing of the session
    upon errors and scope exits.
    """

    __slots__ = BaseSession.__slots__ + (
        '_worker_thread',
    )

    def __init__(self, *, config: APIConfig = None) -> None:
        super().__init__(config=config)
        self._worker_thread = _SyncWorkerThread()
        self._worker_thread.start()

        async def _create_aiohttp_session() -> aiohttp.ClientSession:
            ssl = None
            if self._config.skip_sslcert_validation:
                ssl = False
            connector = aiohttp.TCPConnector(ssl=ssl)
            return aiohttp.ClientSession(connector=connector)

        self.aiohttp_session = self.worker_thread.execute(_create_aiohttp_session())

    def close(self):
        """
        Terminates the session.  It schedules the ``close()`` coroutine
        of the underlying aiohttp session and then enqueues a sentinel
        object to indicate termination.  Then it waits until the worker
        thread to self-terminate by joining.
        """
        if self._closed:
            return
        self._closed = True
        self._worker_thread.execute(_close_aiohttp_session(self.aiohttp_session))
        self._worker_thread.work_queue.put(self.worker_thread.sentinel)
        self._worker_thread.join()

    @property
    def worker_thread(self):
        """
        The thread that internally executes the asynchronous implementations
        of the given API functions.
        """
        return self._worker_thread

    def __enter__(self):
        assert not self.closed, 'Cannot reuse closed session'
        self._context_token = api_session.set(self)
        self.api_version = self.worker_thread.execute(
            _negotiate_api_version(self.aiohttp_session, self.config))
        return self

    def __exit__(self, exc_type, exc_obj, exc_tb):
        self.close()
        api_session.reset(self._context_token)
        return False


class AsyncSession(BaseSession):
    """
    An API client session that makes API requests asynchronously using coroutines.
    You may call all function proxy methods like a coroutine.
    It provides an async context manager interface to ensure closing of the session
    upon errors and scope exits.
    """

    __slots__ = BaseSession.__slots__ + ()

    def __init__(self, *, config: APIConfig = None):
        super().__init__(config=config)

        ssl = None
        if self._config.skip_sslcert_validation:
            ssl = False
        connector = aiohttp.TCPConnector(ssl=ssl)
        self.aiohttp_session = aiohttp.ClientSession(connector=connector)

    async def close(self):
        if self._closed:
            return
        self._closed = True
        await _close_aiohttp_session(self.aiohttp_session)

    async def __aenter__(self):
        assert not self.closed, 'Cannot reuse closed session'
        self._context_token = api_session.set(self)
        self.api_version = await _negotiate_api_version(self.aiohttp_session, self.config)
        return self

    async def __aexit__(self, exc_type, exc_obj, exc_tb):
        await self.close()
        api_session.reset(self._context_token)
        return False
