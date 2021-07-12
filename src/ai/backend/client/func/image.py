from typing import Iterable, Sequence

from .base import api_function, BaseFunction
from ..request import Request
from ..session import api_session

__all__ = (
    'Image',
)


class Image(BaseFunction):
    """
    Provides a shortcut of :func:`Admin.query()
    <ai.backend.client.admin.Admin.query>` that fetches the information about
    available images.
    """

    @api_function
    @classmethod
    async def list(
        cls,
        operation: bool = False,
        fields: Iterable[str] = None,
    ) -> Sequence[dict]:
        """
        Fetches the list of registered images in this cluster.
        """
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
        data = await api_session.get().Admin._query(q, variables)
        return data['images']

    @api_function
    @classmethod
    async def rescan_images(cls, registry: str):
        q = 'mutation($registry: String) {' \
            '  rescan_images(registry:$registry) {' \
            '   ok msg task_id' \
            '  }' \
            '}'
        variables = {
            'registry': registry,
        }
        data = await api_session.get().Admin._query(q, variables)
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
        data = await api_session.get().Admin._query(q, variables)
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
        data = await api_session.get().Admin._query(q, variables)
        return data['dealias_image']

    @api_function
    @classmethod
    async def get_image_import_form(cls) -> dict:
        rqst = Request('GET', '/image/import')
        async with rqst.fetch() as resp:
            data = await resp.json()
        return data

    @api_function
    @classmethod
    async def build(cls, **kwargs) -> dict:
        rqst = Request('POST', '/image/import')
        rqst.set_json(kwargs)
        async with rqst.fetch() as resp:
            data = await resp.json()
        return data
