from abc import abstractmethod
import functools
import inspect

from .compat import Py36Object
from .exceptions import BackendAPIError

__all__ = (
    'BaseFunction',
    'SyncFunctionMixin',
    'AsyncFunctionMixin',
)


class BaseFunction(Py36Object):

    '''
    Implements the request creation and response handling logic,
    while delegating the process of request sending to the subclasses
    via the generator protocol.
    '''

    @abstractmethod
    def _call_base_method(self, meth):
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def _call_base_clsmethod(cls, meth):
        raise NotImplementedError

    @staticmethod
    def _handle_response(resp, meth_gen):
        if resp.status // 100 != 2:
            raise BackendAPIError(resp.status, resp.reason, resp.text())
        try:
            meth_gen.send(resp)
        except StopIteration as e:
            return e.value
        else:
            raise RuntimeError('Invalid state')

    @staticmethod
    async def _handle_response_async(resp, meth_gen):
        if resp.status // 100 != 2:
            raise BackendAPIError(resp.status, resp.reason, await resp.text())
        try:
            meth_gen.send(resp)
        except StopIteration as e:
            return e.value
        else:
            raise RuntimeError('Invalid state')


class SyncFunctionMixin:
    '''
    Synchronous request sender using requests.
    '''

    @staticmethod
    def _make_request(gen):
        rqst = next(gen)
        fetch_ctx = rqst.fetch()
        return fetch_ctx

    @classmethod
    def _call_base_clsmethod(cls, meth):
        assert inspect.ismethod(meth)

        @classmethod
        @functools.wraps(meth)
        def _caller(cls, *args, **kwargs):
            assert cls._session is not None, \
                   'You must use API wrapper functions via a Session object.'
            gen = meth(*args, **kwargs)
            fetch_ctx = cls._make_request(gen)
            with fetch_ctx as resp:
                return cls._handle_response(resp, gen)

        return _caller

    def _call_base_method(self, meth):
        assert inspect.ismethod(meth)

        @functools.wraps(meth)
        def _caller(*args, **kwargs):
            assert type(self)._session is not None, \
                   'You must use API wrapper functions via a Session object.'
            gen = meth(*args, **kwargs)
            fetch_ctx = self._make_request(gen)
            with fetch_ctx as resp:
                return self._handle_response(resp, gen)

        return _caller


class AsyncFunctionMixin:
    '''
    Asynchronous request sender using aiohttp.
    '''

    @staticmethod
    async def _make_request(gen):
        rqst = next(gen)
        fetch_ctx = rqst.fetch()
        return fetch_ctx

    @classmethod
    def _call_base_clsmethod(cls, meth):
        assert inspect.ismethod(meth)

        @classmethod
        @functools.wraps(meth)
        async def _caller(cls, *args, **kwargs):
            assert cls._session is not None, \
                   'You must use API wrapper functions via a Session object.'
            gen = meth(*args, **kwargs)
            fetch_ctx = await cls._make_request(gen)
            async with fetch_ctx as resp:
                return await cls._handle_response_async(resp, gen)

        return _caller

    def _call_base_method(self, meth):
        assert inspect.ismethod(meth)

        @functools.wraps(meth)
        async def _caller(*args, **kwargs):
            assert type(self)._session is not None, \
                   'You must use API wrapper functions via a Session object.'
            gen = meth(*args, **kwargs)
            fetch_ctx = await self._make_request(gen)
            async with fetch_ctx as resp:
                return await self._handle_response_async(resp, gen)

        return _caller
