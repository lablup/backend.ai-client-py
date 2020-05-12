from typing import List, Mapping

from .base import api_function, BaseFunction
from ..request import Request
from ..session import api_session


__all__ = (
    'Dotfile',
)


class Dotfile(BaseFunction):

    @api_function
    @classmethod
    async def create(cls,
                     data: str,
                     path: str,
                     permission: str,
                     owner_access_key: str = None,
                     ) -> 'Dotfile':
        rqst = Request(api_session.get(),
                       'POST', '/user-config/dotfiles')
        body = {
            'data': data,
            'path': path,
            'permission': permission
        }
        rqst.set_json(body)
        async with rqst.fetch() as resp:
            await resp.json()
        return cls(path, owner_access_key=owner_access_key)

    @api_function
    @classmethod
    async def list_dotfiles(cls) -> 'List[Mapping[str, str]]':
        rqst = Request(api_session.get(),
                       'GET', '/user-config/dotfiles')
        async with rqst.fetch() as resp:
            return await resp.json()

    def __init__(self, path: str, owner_access_key: str = None):
        self.path = path
        self.owner_access_key = owner_access_key

    @api_function
    async def get(self) -> str:
        params = {'path': self.path}
        if self.owner_access_key:
            params['owner_access_key'] = self.owner_access_key
        rqst = Request(api_session.get(),
                       'GET', '/user-config/dotfiles',
                       params=params)
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    async def update(self, data: str, permission: str):
        body = {
            'data': data,
            'path': self.path,
            'permission': permission
        }
        if self.owner_access_key:
            body['owner_access_key'] = self.owner_access_key
        rqst = Request(api_session.get(),
                       'PATCH', '/user-config/dotfiles')
        rqst.set_json(body)

        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    async def delete(self):
        params = {'path': self.path}
        if self.owner_access_key:
            params['owner_access_key'] = self.owner_access_key
        rqst = Request(api_session.get(),
                       'DELETE', '/user-config/dotfiles',
                       params=params)

        async with rqst.fetch() as resp:
            return await resp.json()
