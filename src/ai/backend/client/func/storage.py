import textwrap
from typing import (
    Sequence,
)

from .fields import set_default_fields, storage_fields
from .types import FieldSpec, PaginatedResult
from ai.backend.client.session import api_session
from ai.backend.client.pagination import generate_paginated_results
from .base import api_function, BaseFunction

__all__ = (
    'Storage',
)

_default_list_fields_names = (
    'id',
    'backend',
    'capabilities',
)
_default_detail_fields_names = (
    'id',
    'backend',
    'path',
    'fsprefix',
    'capabilities',
    'hardware_metadata',
)

_default_list_fields = set_default_fields(storage_fields, _default_list_fields_names)
_default_detail_fields = set_default_fields(storage_fields, _default_detail_fields_names)


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
        fields: Sequence[FieldSpec] = _default_list_fields,
        page_offset: int = 0,
        page_size: int = 20,
        filter: str = None,
        order: str = None,
    ) -> PaginatedResult[dict]:
        """
        Lists the keypairs.
        You need an admin privilege for this operation.
        """
        return await generate_paginated_results(
            'storage_volume_list',
            {
                'filter': (filter, 'String'),
                'order': (order, 'String'),
            },
            fields,
            page_offset=page_offset,
            page_size=page_size,
        )

    @api_function
    @classmethod
    async def detail(
        cls,
        vfolder_host: str,
        fields: Sequence[FieldSpec] = _default_detail_fields,
    ) -> dict:
        query = textwrap.dedent("""\
            query($vfolder_host: String!) {
                storage_volume(id: $vfolder_host) {$fields}
            }
        """)
        query = query.replace('$fields', ' '.join(f.field_ref for f in fields))
        variables = {'vfolder_host': vfolder_host}
        data = await api_session.get().Admin._query(query, variables)
        return data['storage_volume']
