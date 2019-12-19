from typing import List, Mapping
import yaml

from .base import api_function
from .request import Request


class TaskTemplate:

    session = None
    @api_function
    @classmethod
    async def create(cls, template: str) -> 'TaskTemplate':
        rqst = Request(cls.session,
                       'POST', '/task-template')
        rqst.set_content(
            template.encode(),
            content_type='text/yaml'
        )
        async with rqst.fetch() as resp:
            if resp.status == 200:
                response = await resp.json()

                body = yaml.load(template, Loader=yaml.BaseLoader)
                owner_access_key = body.get('scope', {}).get('owner_access_key', None)
                return cls(response['id'], owner_access_key=owner_access_key)

    @api_function
    @classmethod
    async def list_templates(cls, list_all: bool = False) -> 'List[Mapping[str, str]]':
        rqst = Request(cls.session,
                       'GET', '/task-template')
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
                       'GET', f'/task-template/{self.template_id}',
                       params=params)
        async with rqst.fetch() as resp:
            if resp.status == 200:
                return await resp.text()

    @api_function
    async def put(self, template: str):
        rqst = Request(self.session,
                       'PUT', f'/task-template/{self.template_id}')
        rqst.set_content(
            template.encode(),
            content_type='text/yaml'
        )

        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    async def delete(self):
        rqst = Request(self.session,
                       'DELETE', f'/task-template/{self.template_id}')

        async with rqst.fetch() as resp:
            return await resp.json()
