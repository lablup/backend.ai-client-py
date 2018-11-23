import abc
import asyncio
import threading
import queue

import aiohttp

from .config import APIConfig, get_config


__all__ = (
    'BaseSession',
    'Session',
    'AsyncSession',
)


class _SyncWorkerThread(threading.Thread):

    sentinel = object()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.work_queue = queue.Queue()
        self.done_queue = queue.Queue()

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            while True:
                coro = self.work_queue.get()
                if coro is self.sentinel:
                    break
                try:
                    result = loop.run_until_complete(coro)
                except Exception as e:
                    self.done_queue.put_nowait(e)
                else:
                    self.done_queue.put_nowait(result)
                self.work_queue.task_done()
        except (SystemExit, KeyboardInterrupt):
            pass
        finally:
            loop.close()

    def execute(self, coro):
        self.work_queue.put(coro)
        result = self.done_queue.get()
        self.done_queue.task_done()
        if isinstance(result, Exception):
            raise result
        return result


class BaseSession(metaclass=abc.ABCMeta):
    __slots__ = (
        '_config', '_closed', 'aiohttp_session',
        'Admin', 'Agent', 'Kernel', 'KeyPair', 'VFolder',
    )

    def __init__(self, *, config: APIConfig = None):
        self._closed = False
        self._config = config if config else get_config()

    @abc.abstractmethod
    def close(self):
        raise NotImplementedError

    @property
    def closed(self):
        return self._closed

    @property
    def config(self):
        return self._config


class Session(BaseSession):
    '''
    An API client session that makes API requests synchronously.
    '''

    __slots__ = BaseSession.__slots__ + (
        '_worker_thread',
    )

    def __init__(self, *, config: APIConfig = None):
        '''
        Initialize a API client session.

        :param APIConfig config: The API configuration.  If set to ``None``, it will
                                 use the global configuration which is read from the
                                 environment variables.
        '''
        super().__init__(config=config)
        self._worker_thread = _SyncWorkerThread()
        self._worker_thread.start()

        async def _create_aiohttp_session():
            return aiohttp.ClientSession()

        self.aiohttp_session = self.worker_thread.execute(_create_aiohttp_session())

        from .base import BaseFunction
        from .admin import Admin
        from .agent import Agent
        from .kernel import Kernel
        from .keypair import KeyPair
        from .vfolder import VFolder
        self.Admin = type('Admin', (BaseFunction, ), {
            **Admin.__dict__,
            'session': self,
        })
        self.Agent = type('Agent', (BaseFunction, ), {
            **Agent.__dict__,
            'session': self,
        })
        self.Kernel = type('Kernel', (BaseFunction, ), {
            **Kernel.__dict__,
            'session': self,
        })
        self.KeyPair = type('KeyPair', (BaseFunction, ), {
            **KeyPair.__dict__,
            'session': self,
        })
        self.VFolder = type('VFolder', (BaseFunction, ), {
            **VFolder.__dict__,
            'session': self,
        })

    def close(self):
        if self._closed:
            return
        self._closed = True
        self._worker_thread.work_queue.put(self.aiohttp_session.close())
        self._worker_thread.work_queue.put(self.worker_thread.sentinel)
        self._worker_thread.join()

    @property
    def worker_thread(self):
        return self._worker_thread

    def __enter__(self):
        assert not self.closed, 'Cannot reuse closed session'
        return self

    def __exit__(self, exc_type, exc_obj, exc_tb):
        self.close()
        return False


class AsyncSession(BaseSession):
    '''
    An API client session that makes API requests asynchronously using coroutines.
    '''

    __slots__ = BaseSession.__slots__ + ()

    def __init__(self, *, config: APIConfig = None):
        '''
        Initialize a API client session.

        :param APIConfig config: The API configuration.  If set to ``None``, it will
                                 use the global configuration which is read from the
                                 environment variables.
        '''
        super().__init__(config=config)

        self.aiohttp_session = aiohttp.ClientSession()

        from .base import BaseFunction
        from .admin import Admin
        from .agent import Agent
        from .kernel import Kernel
        from .keypair import KeyPair
        from .vfolder import VFolder
        self.Admin = type('Admin', (BaseFunction, ), {
            **Admin.__dict__,
            'session': self,
        })
        self.Agent = type('Agent', (BaseFunction, ), {
            **Agent.__dict__,
            'session': self,
        })
        self.Kernel = type('Kernel', (BaseFunction, ), {
            **Kernel.__dict__,
            'session': self,
        })
        self.KeyPair = type('KeyPair', (BaseFunction, ), {
            **KeyPair.__dict__,
            'session': self,
        })
        self.VFolder = type('VFolder', (BaseFunction, ), {
            **VFolder.__dict__,
            'session': self,
        })

    async def close(self):
        if self._closed:
            return
        self._closed = True
        await self.aiohttp_session.close()

    async def __aenter__(self):
        assert not self.closed, 'Cannot reuse closed session'
        return self

    async def __aexit__(self, exc_type, exc_obj, exc_tb):
        await self.close()
        return False
