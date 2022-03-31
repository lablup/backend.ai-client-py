from typing import Optional, Sequence

from .fields import set_default_fields, image_fields
from .types import FieldSpec
from .base import api_function, BaseFunction
from ..request import Request
from ..session import api_session

__all__ = (
    'Image',
)

_default_list_fields_admin_names = (
    'name',
    'registry',
    'architecture',
    'tag',
    'digest',
    'size_bytes',
    'aliases',
)
_default_list_fields_admin = set_default_fields(image_fields, _default_list_fields_admin_names)


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
        fields: Sequence[FieldSpec] = _default_list_fields_admin,
    ) -> Sequence[dict]:
        """
        Fetches the list of registered images in this cluster.
        """
        q = 'query($is_operation: Boolean) {' \
            '  images(is_operation: $is_operation) {' \
            '    $fields' \
            '  }' \
            '}'
        q = q.replace('$fields', ' '.join(f.field_ref for f in fields))
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
    async def alias_image(
        cls,
        alias: str,
        target: str,
        arch: Optional[str] = None,
    ) -> dict:
        q = 'mutation($alias: String!, $target: String!) {' \
            '  alias_image(alias: $alias, target: $target) {' \
            '   ok msg' \
            '  }' \
            '}'
        variables = {
            'alias': alias,
            'target': target,
        }
        if arch:
            variables = {'architecture': arch, **variables}
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
