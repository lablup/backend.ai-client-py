from typing import Mapping

from .base import api_function
from ..request import Request

__all__ = (
    'System',
)


class System:
    '''
    Provides the function interface for the API endpoint's system information.
    '''

    @api_function
    @classmethod
    async def get_versions(cls) -> Mapping[str, str]:
        rqst = Request(cls.session, 'GET', '/')
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def get_manager_version(cls) -> str:
        rqst = Request(cls.session, 'GET', '/')
        async with rqst.fetch() as resp:
            ret = await resp.json()
            return ret['manager']

    @api_function
    @classmethod
    async def get_api_version(cls) -> str:
        rqst = Request(cls.session, 'GET', '/')
        async with rqst.fetch() as resp:
            ret = await resp.json()
            return ret['version']
