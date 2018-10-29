from ai.backend.client.base import BaseFunction

from .request import Request


class BaseManager(BaseFunction):

    _session = None

    @classmethod
    def _freeze(cls):
        resp = yield Request(cls._session, 'PUT', '/manager/status', {
            'status': 'frozen',
        })
        assert resp.status == 204

    @classmethod
    def _unfreeze(cls):
        resp = yield Request(cls._session, 'PUT', '/manager/status', {
            'status': 'running',
        })
        assert resp.status == 204

    def __init_subclass__(cls):
        cls.freeze = cls._call_base_clsmethod(cls._freeze)
        cls.unfreeze = cls._call_base_clsmethod(cls._unfreeze)
