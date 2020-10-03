from typing import (
    Any,
    AsyncIterator,
    Dict,
    Iterable,
    Sequence,
    Union,
)

from .base import api_function, BaseFunction
from ..request import Request
from ..pagination import generate_paginated_results

__all__ = (
    'KeyPair',
)

_default_list_fields = (
    'access_key',
    'secret_key',
    'is_active',
    'is_admin',
    'created_at',
)


class KeyPair(BaseFunction):
    """
    Provides interactions with keypairs.
    """

    def __init__(self, access_key: str):
        self.access_key = access_key

    @api_function
    @classmethod
    async def create(cls, user_id: Union[int, str],
                     is_active: bool = True,
                     is_admin: bool = False,
                     resource_policy: str = None,
                     rate_limit: int = None,
                     fields: Iterable[str] = None) -> dict:
        """
        Creates a new keypair with the given options.
        You need an admin privilege for this operation.
        """
        if fields is None:
            fields = ('access_key', 'secret_key')
        uid_type = 'Int!' if isinstance(user_id, int) else 'String!'
        q = 'mutation($user_id: {0}, $input: KeyPairInput!) {{'.format(uid_type) + \
            '  create_keypair(user_id: $user_id, props: $input) {' \
            '    ok msg keypair { $fields }' \
            '  }' \
            '}'
        q = q.replace('$fields', ' '.join(fields))
        variables = {
            'user_id': user_id,
            'input': {
                'is_active': is_active,
                'is_admin': is_admin,
                'resource_policy': resource_policy,
                'rate_limit': rate_limit,
            },
        }
        rqst = Request('POST', '/admin/graphql')
        rqst.set_json({
            'query': q,
            'variables': variables,
        })
        async with rqst.fetch() as resp:
            data = await resp.json()
            return data['create_keypair']

    @api_function
    @classmethod
    async def update(cls, access_key: str,
                     is_active: bool = None,
                     is_admin: bool = None,
                     resource_policy: str = None,
                     rate_limit: int = None) -> dict:
        """
        Creates a new keypair with the given options.
        You need an admin privilege for this operation.
        """
        q = 'mutation($access_key: String!, $input: ModifyKeyPairInput!) {' + \
            '  modify_keypair(access_key: $access_key, props: $input) {' \
            '    ok msg' \
            '  }' \
            '}'
        variables = {
            'access_key': access_key,
            'input': {
                'is_active': is_active,
                'is_admin': is_admin,
                'resource_policy': resource_policy,
                'rate_limit': rate_limit,
            },
        }
        rqst = Request('POST', '/admin/graphql')
        rqst.set_json({
            'query': q,
            'variables': variables,
        })
        async with rqst.fetch() as resp:
            data = await resp.json()
            return data['modify_keypair']

    @api_function
    @classmethod
    async def delete(cls, access_key: str):
        """
        Deletes an existing keypair with given ACCESSKEY.
        """
        q = 'mutation($access_key: String!) {' \
            '  delete_keypair(access_key: $access_key) {' \
            '    ok msg' \
            '  }' \
            '}'
        variables = {
            'access_key': access_key,
        }
        rqst = Request('POST', '/admin/graphql')
        rqst.set_json({
            'query': q,
            'variables': variables,
        })
        async with rqst.fetch() as resp:
            data = await resp.json()
            return data['delete_keypair']

    @api_function
    @classmethod
    async def list(
        cls, user_id: Union[int, str] = None,
        is_active: bool = None,
        fields: Sequence[str] = _default_list_fields,
    ) -> Sequence[dict]:
        """
        Lists the keypairs.
        You need an admin privilege for this operation.
        """
        if user_id is None:
            q = 'query($is_active: Boolean) {' \
                '  keypairs(is_active: $is_active) {' \
                '    $fields' \
                '  }' \
                '}'
        else:
            uid_type = 'Int!' if isinstance(user_id, int) else 'String!'
            q = 'query($email: {0}, $is_active: Boolean) {{'.format(uid_type) + \
                '  keypairs(email: $email, is_active: $is_active) {' \
                '    $fields' \
                '  }' \
                '}'
        q = q.replace('$fields', ' '.join(fields))
        variables: Dict[str, Any] = {
            'is_active': is_active,
        }
        if user_id is not None:
            variables['email'] = user_id
        rqst = Request('POST', '/admin/graphql')
        rqst.set_json({
            'query': q,
            'variables': variables,
        })
        async with rqst.fetch() as resp:
            data = await resp.json()
            return data['keypairs']

    @api_function
    @classmethod
    async def paginated_list(
        cls,
        is_active: bool = None,
        domain_name: str = None,
        *,
        user_id: str = None,
        fields: Sequence[str] = _default_list_fields,
        page_size: int = 20,
    ) -> AsyncIterator[dict]:
        """
        Lists the keypairs.
        You need an admin privilege for this operation.
        """
        variables = {
            'is_active': (is_active, 'Boolean'),
            'domain_name': (domain_name, 'String'),
        }
        if user_id is not None:
            variables['email'] = (user_id, 'String')
        async for item in generate_paginated_results(
            'keypair_list',
            variables,
            fields,
            page_size=page_size,
        ):
            yield item

    @api_function
    async def info(self, fields: Iterable[str] = None) -> dict:
        """
        Returns the keypair's information such as resource limits.

        :param fields: Additional per-agent query fields to fetch.

        .. versionadded:: 18.12
        """
        if fields is None:
            fields = (
                'access_key', 'secret_key',
                'is_active', 'is_admin',
            )
        q = 'query {' \
            '  keypair {' \
            '    $fields' \
            '  }' \
            '}'
        q = q.replace('$fields', ' '.join(fields))
        rqst = Request('POST', '/admin/graphql')
        rqst.set_json({
            'query': q,
        })
        async with rqst.fetch() as resp:
            data = await resp.json()
            return data['keypair']

    @api_function
    @classmethod
    async def activate(cls, access_key: str) -> dict:
        """
        Activates this keypair.
        You need an admin privilege for this operation.
        """
        q = 'mutation($access_key: String!, $input: ModifyKeyPairInput!) {' + \
            '  modify_keypair(access_key: $access_key, props: $input) {' \
            '    ok msg' \
            '  }' \
            '}'
        variables = {
            'access_key': access_key,
            'input': {
                'is_active': True,
                'is_admin': None,
                'resource_policy': None,
                'rate_limit': None,
            },
        }
        rqst = Request('POST', '/admin/graphql')
        rqst.set_json({
            'query': q,
            'variables': variables,
        })
        async with rqst.fetch() as resp:
            data = await resp.json()
            return data['modify_keypair']

    @api_function
    @classmethod
    async def deactivate(cls, access_key: str) -> dict:
        """
        Deactivates this keypair.
        Deactivated keypairs cannot make any API requests
        unless activated again by an administrator.
        You need an admin privilege for this operation.
        """
        q = 'mutation($access_key: String!, $input: ModifyKeyPairInput!) {' + \
            '  modify_keypair(access_key: $access_key, props: $input) {' \
            '    ok msg' \
            '  }' \
            '}'
        variables = {
            'access_key': access_key,
            'input': {
                'is_active': False,
                'is_admin': None,
                'resource_policy': None,
                'rate_limit': None,
            },
        }
        rqst = Request('POST', '/admin/graphql')
        rqst.set_json({
            'query': q,
            'variables': variables,
        })
        async with rqst.fetch() as resp:
            data = await resp.json()
            return data['modify_keypair']
