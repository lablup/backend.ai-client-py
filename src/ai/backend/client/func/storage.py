import textwrap
from typing import (
    AsyncIterator,
    Sequence,
)

from .base import api_function, BaseFunction
from ..request import Request
from ..pagination import generate_paginated_results

__all__ = (
    'Storage',
)

_default_list_fields = (
    'id',
    'backend',
    'capabilities',
)

_default_detail_fields = (
    'id',
    'backend',
    'path',
    'fsprefix',
    'capabilities',
    'hardware_metadata',
)


class Storage(BaseFunction):
    """
    Provides a shortcut of :func:`Admin.query()
    <ai.backend.client.admin.Admin.query>` that fetches various straoge volume
    information keyed by vfolder hosts.

    .. note::

      All methods in this function class require your API access key to
      have the *super-admin* privilege.
    """

    @api_function
    @classmethod
    async def paginated_list(
        cls,
        status: str = 'ALIVE',
        *,
        fields: Sequence[str] = _default_list_fields,
        page_size: int = 20,
    ) -> AsyncIterator[dict]:
        """
        Lists the keypairs.
        You need an admin privilege for this operation.
        """
        async for item in generate_paginated_results(
            'storage_volume_list',
            {},
            fields,
            page_size=page_size,
        ):
            yield item

    @api_function
    @classmethod
    async def detail(
        cls,
        vfolder_host: str,
        fields: Sequence[str] = _default_detail_fields,
    ) -> dict:
        query = textwrap.dedent("""\
            query($vfolder_host: String!) {
                storage_volume(id: $vfolder_host) {$fields}
            }
        """)
        query = query.replace('$fields', ' '.join(fields))
        variables = {'vfolder_host': vfolder_host}
        rqst = Request('POST', '/admin/graphql')
        rqst.set_json({
            'query': query,
            'variables': variables,
        })
        async with rqst.fetch() as resp:
            data = await resp.json()
            return data['storage_volume']
