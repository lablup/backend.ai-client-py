from ai.backend.client.base import BaseFunction

from .request import Request


class BaseManager(BaseFunction):

    _session = None

    @classmethod
    def _status(cls):
        resp = yield Request(cls._session, 'GET', '/manager/status', {
            'status': 'running',
        })
        return resp.json()

    @classmethod
    def _freeze(cls, force_kill=False):
        resp = yield Request(cls._session, 'PUT', '/manager/status', {
            'status': 'frozen',
            'force_kill': force_kill,
        })
        assert resp.status == 204

    @classmethod
    def _unfreeze(cls):
        resp = yield Request(cls._session, 'PUT', '/manager/status', {
            'status': 'running',
        })
        assert resp.status == 204

    def __init_subclass__(cls):
        cls.status = cls._call_base_clsmethod(cls._status)
        cls.freeze = cls._call_base_clsmethod(cls._freeze)
        cls.unfreeze = cls._call_base_clsmethod(cls._unfreeze)
