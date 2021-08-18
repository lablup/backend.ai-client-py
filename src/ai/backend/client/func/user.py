from __future__ import annotations

import enum
import textwrap
from typing import AsyncIterator, Iterable, Sequence, Union
import uuid

from .base import api_function, BaseFunction
from ..auth import AuthToken, AuthTokenTypes
from ..request import Request
from ..session import api_session
from ..pagination import generate_paginated_results

__all__ = (
    'User',
    'UserStatus',
    'UserRole',
)

_default_list_fields = (
    'uuid',
    'role',
    'username',
    'email',
    'is_active',
    'created_at',
    'domain_name',
    'groups',
)


class UserRole(str, enum.Enum):
    """
    The role (privilege level) of users.
    """
    SUPERADMIN = 'superadmin'
    ADMIN = 'admin'
    USER = 'user'
    MONITOR = 'monitor'


class UserStatus(enum.Enum):
    """
    The detailed status of users to represent the signup process and account lifecycles.
    """
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    DELETED = 'deleted'
    BEFORE_VERIFICATION = 'before-verification'


class User(BaseFunction):
    """
    Provides interactions with users.
    """

    @api_function
    @classmethod
    async def authorize(cls, username: str, password: str, *,
                        token_type: AuthTokenTypes = AuthTokenTypes.KEYPAIR) -> AuthToken:
        """
        Authorize the given credentials and get the API authentication token.
        This function can be invoked anonymously; i.e., it does not require
        access/secret keys in the session config as its purpose is to "get" them.

        Its functionality will be expanded in the future to support multiple types
        of authentication methods.
        """
        rqst = Request('POST', '/auth/authorize')
        rqst.set_json({
            'type': token_type.value,
            'domain': api_session.get().config.domain,
            'username': username,
            'password': password,
        })
        async with rqst.fetch() as resp:
            data = await resp.json()
            return AuthToken(
                type=token_type,
                content=data['data'],
            )

    @api_function
    @classmethod
    async def list(
        cls,
        status: str = None,
        group: str = None,
        fields: Sequence[str] = _default_list_fields,
    ) -> Sequence[dict]:
        """
        Fetches the list of users. Domain admins can only get domain users.

        :param status: Fetches users in a specific status
                       (active, inactive, deleted, before-verification).
        :param group: Fetch users in a specific group.
        :param fields: Additional per-user query fields to fetch.
        """
        query = textwrap.dedent("""\
            query($status: String, $group: UUID) {
                users(status: $status, group_id: $group) {$fields}
            }
        """)
        query = query.replace('$fields', ' '.join(fields))
        variables = {
            'status': status,
            'group': group,
        }
        data = await api_session.get().Admin._query(query, variables)
        return data['users']

    @api_function
    @classmethod
    async def paginated_list(
        cls,
        status: str = None,
        group: str = None,
        *,
        fields: Sequence[str] = _default_list_fields,
        page_size: int = 20,
        filter: str = None,
        order: str = None,
    ) -> AsyncIterator[dict]:
        """
        Fetches the list of users. Domain admins can only get domain users.

        :param status: Fetches users in a specific status
                       (active, inactive, deleted, before-verification).
        :param group: Fetch users in a specific group.
        :param fields: Additional per-user query fields to fetch.
        """
        async for item in generate_paginated_results(
            'user_list',
            {
                'status': (status, 'String'),
                'group_id': (group, 'UUID'),
                'filter': (filter, 'String'),
                'order': (order, 'String'),
            },
            fields,
            page_size=page_size,
        ):
            yield item

    @api_function
    @classmethod
    async def detail(cls, email: str = None, fields: Iterable[str] = None) -> Sequence[dict]:
        """
        Fetch information of a user. If email is not specified,
        requester's information will be returned.

        :param email: Email of the user to fetch.
        :param fields: Additional per-user query fields to fetch.
        """
        if fields is None:
            fields = ('uuid', 'username', 'email', 'need_password_change', 'status', 'status_info',
                      'created_at', 'domain_name', 'role')
        if email is None:
            query = textwrap.dedent("""\
                query {
                    user {$fields}
                }
            """)
        else:
            query = textwrap.dedent("""\
                query($email: String) {
                    user(email: $email) {$fields}
                }
            """)
        query = query.replace('$fields', ' '.join(fields))
        variables = {'email': email}
        data = await api_session.get().Admin._query(query, variables if email is not None else None)
        return data['user']

    @api_function
    @classmethod
    async def detail_by_uuid(
        cls,
        user_uuid: Union[str, uuid.UUID] = None,
        fields: Iterable[str] = None,
    ) -> Sequence[dict]:
        """
        Fetch information of a user by user's uuid. If user_uuid is not specified,
        requester's information will be returned.

        :param user_uuid: UUID of the user to fetch.
        :param fields: Additional per-user query fields to fetch.
        """
        if fields is None:
            fields = ('uuid', 'username', 'email', 'need_password_change', 'status', 'status_info',
                      'created_at', 'domain_name', 'role')
        if user_uuid is None:
            query = textwrap.dedent("""\
                query {
                    user {$fields}
                }
            """)
        else:
            query = textwrap.dedent("""\
                query($user_id: ID) {
                    user_from_uuid(user_id: $user_id) {$fields}
                }
            """)
        query = query.replace('$fields', ' '.join(fields))
        variables = {'user_id': str(user_uuid)}
        data = await api_session.get().Admin._query(query, variables if user_uuid is not None else None)
        return data['user_from_uuid']

    @api_function
    @classmethod
    async def create(
        cls,
        domain_name: str,
        email: str,
        password: str,
        username: str = None,
        full_name: str = None,
        role: UserRole | str = UserRole.USER,
        status: UserStatus | str = UserStatus.ACTIVE,
        need_password_change: bool = False,
        description: str = '',
        group_ids: Iterable[str] = None,
        fields: Iterable[str] = None
    ) -> dict:
        """
        Creates a new user with the given options.
        You need an admin privilege for this operation.
        """
        if fields is None:
            fields = ('domain_name', 'email', 'username',)
        query = textwrap.dedent("""\
            mutation($email: String!, $input: UserInput!) {
                create_user(email: $email, props: $input) {
                    ok msg user {$fields}
                }
            }
        """)
        query = query.replace('$fields', ' '.join(fields))
        variables = {
            'email': email,
            'input': {
                'password': password,
                'username': username,
                'full_name': full_name,
                'role': role.value if isinstance(role, UserRole) else role,
                'status': status.value if isinstance(status, UserStatus) else status,
                'need_password_change': need_password_change,
                'description': description,
                'domain_name': domain_name,
                'group_ids': group_ids,
            },
        }
        data = await api_session.get().Admin._query(query, variables)
        return data['create_user']

    @api_function
    @classmethod
    async def update(
        cls,
        email: str,
        password: str = None, username: str = None,
        full_name: str = None,
        domain_name: str = None,
        role: UserRole | str = UserRole.USER,
        status: UserStatus | str = UserStatus.ACTIVE,
        need_password_change: bool = None,
        description: str = None,
        group_ids: Iterable[str] = None,
        fields: Iterable[str] = None
    ) -> dict:
        """
        Update existing user.
        You need an admin privilege for this operation.
        """
        query = textwrap.dedent("""\
            mutation($email: String!, $input: ModifyUserInput!) {
                modify_user(email: $email, props: $input) {
                    ok msg
                }
            }
        """)
        variables = {
            'email': email,
            'input': {
                'password': password,
                'username': username,
                'full_name': full_name,
                'domain_name': domain_name,
                'role': role.value if isinstance(role, UserRole) else role,
                'status': status.value if isinstance(status, UserStatus) else status,
                'need_password_change': need_password_change,
                'description': description,
                'group_ids': group_ids,
            },
        }
        data = await api_session.get().Admin._query(query, variables)
        return data['modify_user']

    @api_function
    @classmethod
    async def delete(cls, email: str):
        """
        Inactivates an existing user.
        """
        query = textwrap.dedent("""\
            mutation($email: String!) {
                delete_user(email: $email) {
                    ok msg
                }
            }
        """)
        variables = {'email': email}
        data = await api_session.get().Admin._query(query, variables)
        return data['delete_user']

    @api_function
    @classmethod
    async def purge(cls, email: str, purge_shared_vfolders=False):
        """
        Deletes an existing user.

        User's virtual folders are also deleted, except the ones shared with other users.
        Shared virtual folder's ownership will be transferred to the requested admin.
        To delete shared folders as well, set ``purge_shared_vfolders`` to ``True``.
        """
        query = textwrap.dedent("""\
            mutation($email: String!, $input: PurgeUserInput!) {
                purge_user(email: $email, props: $input) {
                    ok msg
                }
            }
        """)
        variables = {
            'email': email,
            'input': {
                'purge_shared_vfolders': purge_shared_vfolders,
            },
        }
        data = await api_session.get().Admin._query(query, variables)
        return data['purge_user']
