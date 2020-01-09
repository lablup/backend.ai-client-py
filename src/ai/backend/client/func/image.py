from typing import Iterable, Sequence

from ai.backend.client.func.base import api_function
from ai.backend.client.request import Request

__all__ = (
    'Image',
)


class Image:
    '''
    Provides a shortcut of :func:`Admin.query()
    <ai.backend.client.admin.Admin.query>` that fetches the information about
    available images.
    '''

    session = None
    '''The client session instance that this function class is bound to.'''

    @api_function
    @classmethod
    async def list(cls,
                   operation: bool = False,
                   fields: Iterable[str] = None) -> Sequence[dict]:
        '''
        Fetches the list of registered images in this cluster.
        '''

        if fields is None:
            fields = (
                'name',
                'tag',
                'hash',
            )
        q = 'query($is_operation: Boolean) {' \
            '  images(is_operation: $is_operation) {' \
            '    $fields' \
            '  }' \
            '}'
        q = q.replace('$fields', ' '.join(fields))
        variables = {
            'is_operation': operation,
        }
        rqst = Request(cls.session, 'POST', '/admin/graphql')
        rqst.set_json({
            'query': q,
            'variables': variables,
        })
        async with rqst.fetch() as resp:
            data = await resp.json()
            return data['images']

    @api_function
    @classmethod
    async def rescan_images(cls, registry: str):
        q = 'mutation($registry: String) {' \
            '  rescan_images(registry:$registry) {' \
            '   ok msg' \
            '  }' \
            '}'
        variables = {
            'registry': registry,
        }
        rqst = Request(cls.session, 'POST', '/admin/graphql')
        rqst.set_json({
            'query': q,
            'variables': variables,
        })
        async with rqst.fetch() as resp:
            data = await resp.json()
            return data['rescan_images']

    @api_function
    @classmethod
    async def alias_image(cls, alias: str, target: str) -> dict:
        q = 'mutation($alias: String!, $target: String!) {' \
            '  alias_image(alias: $alias, target: $target) {' \
            '   ok msg' \
            '  }' \
            '}'
        variables = {
            'alias': alias,
            'target': target,
        }
        rqst = Request(cls.session, 'POST', '/admin/graphql')
        rqst.set_json({
            'query': q,
            'variables': variables,
        })
        async with rqst.fetch() as resp:
            data = await resp.json()
            return data['alias_image']

    @api_function
    @classmethod
    async def dealias_image(cls, alias: str) -> dict:
        q = 'mutation($alias: String!) {' \
            '  dealias_image(alias: $alias) {' \
            '   ok msg' \
            '  }' \
            '}'
        variables = {
            'alias': alias,
        }
        rqst = Request(cls.session, 'POST', '/admin/graphql')
        rqst.set_json({
            'query': q,
            'variables': variables,
        })
        async with rqst.fetch() as resp:
            data = await resp.json()
            return data['dealias_image']

    @api_function
    @classmethod
    async def get_image_import_form(cls) -> dict:
        rqst = Request(cls.session, 'GET', '/image/import')
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def build(cls, **kwargs) -> dict:
        rqst = Request(cls.session, 'POST', '/image/import')
        rqst.set_json(kwargs)
        async with rqst.fetch() as resp:
            return await resp.json()
