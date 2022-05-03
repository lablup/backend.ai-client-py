from __future__ import annotations

import enum
import textwrap
from typing import (
    Iterable,
    Sequence,
    Union,
    Dict,
)
import uuid

from ai.backend.client.auth import AuthToken, AuthTokenTypes
from ai.backend.client.request import Request
from ai.backend.client.session import api_session
from ai.backend.client.output.fields import auditlog_fields
from ai.backend.client.output.types import FieldSpec, PaginatedResult
from ai.backend.client.pagination import generate_paginated_results
from .base import api_function, BaseFunction

__all__ = (
    'AuditLog',

)


_default_list_fields = [
        auditlog_fields['user_id'],
        auditlog_fields['access_key'],
        auditlog_fields['email'],
        auditlog_fields['action'],
        auditlog_fields['data'],
        auditlog_fields['target'],
        auditlog_fields['created_at'],
]


class AuditLog(BaseFunction):
    """
    Provides management of audit logs.
    """
    @api_function
    @classmethod
    async def list(cls, list_all=False):
        rqst = Request('GET', '/audit_logs')
        rqst.set_json({'all': list_all})
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def paginated_list(
        cls,
        user_id: Union[str, str] = None,
        *,
        fields: Sequence[FieldSpec] = _default_list_fields,
        page_offset: int = 0,
        page_size: int = 20,
        filter: str = None,
        order: str = None,
    ) -> PaginatedResult[dict]:
        """
        Fetches the list of audit logs.

        :param user_id: Fetches audit log from a user

        """
        variables = {
            'user_id': (user_id, 'String'),  # list by user_id
            'filter': (filter, 'String'),
            'order': (order, 'String'),
        }

        return await generate_paginated_results(
            'auditlog_list',
            variables,
            fields,
            page_offset=page_offset,
            page_size=page_size,
        )

    @api_function
    @classmethod
    async def create(
        cls,
        user_id: Union[str, str] = None,
        access_key: str = None,
        user_email: str = None,
        data_before: Dict[str, str] = None,
        data_after: Dict[str, str] = None,
        target: str = None,
        action: str = None
    ) -> dict:
        """
        Creates a new audit log entry.
        """

        query = textwrap.dedent("""\
            mutation($input: AuditLogInput!) {
                create_audit_logs(props: $input) {
                    ok msg  
                }
            }
        """)

        variables = {
            'input': {
                'user_id': user_id,
                'access_key': access_key,
                'user_email': user_email,
                'data_before': data_before,
                'data_after': data_after,
                'target': target,
                'action': action
            }


        }

        data = await api_session.get().Admin._query(query, variables)
        return data['create_audit_logs']
