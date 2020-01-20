from typing import List, Mapping

from .base import api_function
from ..request import Request


__all__ = (
    'Dotfile',
)


class Dotfile:

    session = None
    @api_function
    @classmethod
    async def create(cls,
                     data: str,
                     path: str,
                     permission: str,
                     owner_access_key: str = None,
                     ) -> 'Dotfile':
        rqst = Request(cls.session,
                       'POST', '/user-config/dotfiles')
        body = {
            'data': data,
            'path': path,
            'permission': permission
        }
        rqst.set_json(body)
        async with rqst.fetch() as resp:
            if resp.status == 200:
                await resp.json()
                return cls(path, owner_access_key=owner_access_key)

    @api_function
    @classmethod
    async def list_dotfiles(cls) -> 'List[Mapping[str, str]]':
        rqst = Request(cls.session,
                       'GET', '/user-config/dotfiles')
        async with rqst.fetch() as resp:
            if resp.status == 200:
                return await resp.json()

    def __init__(self, path: str, owner_access_key: str = None):
        self.path = path
        self.owner_access_key = owner_access_key

    @api_function
    async def get(self) -> str:
        params = {'path': self.path}
        if self.owner_access_key:
            params['owner_access_key'] = self.owner_access_key
        rqst = Request(self.session,
                       'GET', f'/user-config/dotfiles',
                       params=params)
        async with rqst.fetch() as resp:
            if resp.status == 200:
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
        rqst = Request(self.session,
                       'PATCH', f'/user-config/dotfiles')
        rqst.set_json(body)

        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    async def delete(self):
        params = {'path': self.path}
        if self.owner_access_key:
            params['owner_access_key'] = self.owner_access_key
        rqst = Request(self.session,
                       'DELETE', f'/user-config/dotfiles',
                       params=params)

        async with rqst.fetch() as resp:
            return await resp.json()
