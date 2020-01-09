from .base import api_function
from ..request import Request


class Manager:
    '''
    Provides controlling of the gateway/manager servers.

    .. versionadded:: 18.12
    '''

    session = None
    '''The client session instance that this function class is bound to.'''

    @api_function
    @classmethod
    async def status(cls):
        '''
        Returns the current status of the configured API server.
        '''
        rqst = Request(cls.session, 'GET', '/manager/status')
        rqst.set_json({
            'status': 'running',
        })
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def freeze(cls, force_kill: bool = False):
        '''
        Freezes the configured API server.
        Any API clients will no longer be able to create new compute sessions nor
        create and modify vfolders/keypairs/etc.
        This is used to enter the maintenance mode of the server for unobtrusive
        manager and/or agent upgrades.

        :param force_kill: If set ``True``, immediately shuts down all running
            compute sessions forcibly. If not set, clients who have running compute
            session are still able to interact with them though they cannot create
            new compute sessions.
        '''
        rqst = Request(cls.session, 'PUT', '/manager/status')
        rqst.set_json({
            'status': 'frozen',
            'force_kill': force_kill,
        })
        async with rqst.fetch() as resp:
            assert resp.status == 204

    @api_function
    @classmethod
    async def unfreeze(cls):
        '''
        Unfreezes the configured API server so that it resumes to normal operation.
        '''
        rqst = Request(cls.session, 'PUT', '/manager/status')
        rqst.set_json({
            'status': 'running',
        })
        async with rqst.fetch() as resp:
            assert resp.status == 204
