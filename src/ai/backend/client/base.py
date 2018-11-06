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


class SyncFunctionMixin:
    '''
    Synchronous request sender using requests.
    '''
    _async = False

    @staticmethod
    def _make_request(gen):
        rqst = next(gen)
        resp = rqst.fetch()
        return resp

    @classmethod
    def _call_base_clsmethod(cls, meth):
        assert inspect.ismethod(meth)

        @classmethod
        @functools.wraps(meth)
        def _caller(cls, *args, **kwargs):
            assert cls._session is not None, \
                   'You must use API wrapper functions via a Session object.'
            gen = meth(*args, **kwargs)
            resp = cls._make_request(gen)
            return cls._handle_response(resp, gen)

        return _caller

    def _call_base_method(self, meth):
        assert inspect.ismethod(meth)

        @functools.wraps(meth)
        def _caller(*args, **kwargs):
            assert type(self)._session is not None, \
                   'You must use API wrapper functions via a Session object.'
            gen = meth(*args, **kwargs)
            resp = self._make_request(gen)
            return self._handle_response(resp, gen)

        return _caller


class AsyncFunctionMixin:
    '''
    Asynchronous request sender using aiohttp.
    '''
    _async = True

    @staticmethod
    async def _make_request(gen):
        rqst = next(gen)
        resp = await rqst.afetch()
        return resp

    @classmethod
    def _call_base_clsmethod(cls, meth):
        assert inspect.ismethod(meth)

        @classmethod
        @functools.wraps(meth)
        async def _caller(cls, *args, **kwargs):
            assert cls._session is not None, \
                   'You must use API wrapper functions via a Session object.'
            gen = meth(*args, **kwargs)
            resp = await cls._make_request(gen)
            return cls._handle_response(resp, gen)

        return _caller

    def _call_base_method(self, meth):
        assert inspect.ismethod(meth)

        @functools.wraps(meth)
        async def _caller(*args, **kwargs):
            assert type(self)._session is not None, \
                   'You must use API wrapper functions via a Session object.'
            gen = meth(*args, **kwargs)
            resp = await self._make_request(gen)
            return self._handle_response(resp, gen)

        return _caller
