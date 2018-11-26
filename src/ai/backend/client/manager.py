from ai.backend.client.base import api_function

from .request import Request


class Manager:

    session = None

    @api_function
    @classmethod
    async def status(cls):
        rqst = Request(cls._session, 'GET', '/manager/status')
        rqst.set_json({
            'status': 'running',
        })
        async with rqst.fetch() as resp:
            return resp.json()

    @api_function
    @classmethod
    async def freeze(cls, force_kill=False):
        rqst = Request(cls._session, 'PUT', '/manager/status')
        rqst.set_json({
            'status': 'frozen',
            'force_kill': force_kill,
        })
        async with rqst.fetch() as resp:
            assert resp.status == 204

    @api_function
    @classmethod
    async def unfreeze(cls):
        rqst = Request(cls._session, 'PUT', '/manager/status')
        rqst.set_json({
            'status': 'running',
        })
        async with rqst.fetch() as resp:
            assert resp.status == 204
