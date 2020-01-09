from typing import List, Mapping

from .base import api_function
from ..request import Request


class SessionTemplate:

    session = None
    @api_function
    @classmethod
    async def create(cls,
                     template: str,
                     domain_name: str = None,
                     group_name: str = None,
                     owner_access_key: str = None,
                     ) -> 'SessionTemplate':
        rqst = Request(cls.session,
                       'POST', '/template/session')
        if domain_name is None:
            # Even if config.domain is None, it can be guessed in the manager by user information.
            domain_name = cls.session.config.domain
        if group_name is None:
            group_name = cls.session.config.group
        body = {
            'payload': template,
            'group_name': group_name,
            'domain_name': domain_name,
            'owner_access_key': owner_access_key
        }
        rqst.set_json(body)
        async with rqst.fetch() as resp:
            if resp.status == 200:
                response = await resp.json()

                return cls(response['id'], owner_access_key=owner_access_key)

    @api_function
    @classmethod
    async def list_templates(cls, list_all: bool = False) -> 'List[Mapping[str, str]]':
        rqst = Request(cls.session,
                       'GET', '/template/session')
        rqst.set_json({'all': list_all})
        async with rqst.fetch() as resp:
            if resp.status == 200:
                return await resp.json()

    def __init__(self, template_id: str, owner_access_key: str = None):
        self.template_id = template_id
        self.owner_access_key = owner_access_key

    @api_function
    async def get(self, body_format: str = 'yaml') -> str:
        params = {'format': body_format}
        if self.owner_access_key:
            params['owner_access_key'] = self.owner_access_key
        rqst = Request(self.session,
                       'GET', f'/template/session/{self.template_id}',
                       params=params)
        async with rqst.fetch() as resp:
            if resp.status == 200:
                return await resp.text()

    @api_function
    async def put(self, template: str):
        body = {
            'payload': template
        }
        if self.owner_access_key:
            body['owner_access_key'] = self.owner_access_key
        rqst = Request(self.session,
                       'PUT', f'/template/session/{self.template_id}')
        rqst.set_json(body)

        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    async def delete(self):
        params = {}
        if self.owner_access_key:
            params['owner_access_key'] = self.owner_access_key
        rqst = Request(self.session,
                       'DELETE', f'/template/session/{self.template_id}',
                       params=params)

        async with rqst.fetch() as resp:
            return await resp.json()
