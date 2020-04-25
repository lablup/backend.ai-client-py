import textwrap
from typing import Iterable, Sequence

from .base import api_function
from ..request import Request

__all__ = (
    'ServerLog',
)


class ServerLog:
    '''
    Provides a shortcut of :func:`Admin.query()
    <ai.backend.client.admin.Admin.query>` that fetches various server logs.
    '''

    session = None
    '''The client session instance that this function class is bound to.'''

    @api_function
    @classmethod
    async def list(cls, mark_read: bool = False, page_size: int = 20, page_no: int = 1) -> Sequence[dict]:
        '''
        Fetches server (error) logs.

        :param mark_read: Mark read flog for server logs being fetched.
        :param page_size: Number of logs to fetch (from latest log).
        :param page_no: Page number to fetch.
        '''
        params = {
            'mark_read': str(mark_read),
            'page_size': page_size,
            'page_no': page_no,
        }
        rqst = Request(cls.session, 'GET', '/logs/error', params=params)
        async with rqst.fetch() as resp:
            return await resp.json()
