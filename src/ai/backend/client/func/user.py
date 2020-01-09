import textwrap
from typing import Iterable, Sequence

from .base import api_function
from ..request import Request
from ..auth import AuthToken, AuthTokenTypes

__all__ = (
    'User',
)


class User:
    '''
    Provides interactions with users.
    '''

    session = None
    '''The client session instance that this function class is bound to.'''

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
        rqst = Request(cls.session, 'POST', '/auth/authorize')
        rqst.set_json({
            'type': token_type.value,
            'domain': cls.session.config.domain,
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
    async def list(cls, is_active: bool = None, fields: Iterable[str] = None) -> Sequence[dict]:
        '''
        Fetches the list of users. Domain admins can only get domain users.

        :param is_active: Fetches active or inactive users only if not None.
        :param fields: Additional per-user query fields to fetch.
        '''
        if fields is None:
            fields = ('uuid', 'username', 'email', 'need_password_change', 'is_active',
                      'created_at', 'domain_name', 'role')
        query = textwrap.dedent('''\
            query($is_active: Boolean) {
                users(is_active: $is_active) {$fields}
            }
        ''')
        query = query.replace('$fields', ' '.join(fields))
        variables = {'is_active': is_active}
        rqst = Request(cls.session, 'POST', '/admin/graphql')
        rqst.set_json({
            'query': query,
            'variables': variables,
        })
        async with rqst.fetch() as resp:
            data = await resp.json()
            return data['users']

    @api_function
    @classmethod
    async def detail(cls, email: str = None, fields: Iterable[str] = None) -> Sequence[dict]:
        '''
        Fetch information of a user. If email is not specified,
        requester's information will be returned.

        :param email: Email of the user to fetch.
        :param fields: Additional per-user query fields to fetch.
        '''
        if fields is None:
            fields = ('uuid', 'username', 'email', 'need_password_change', 'is_active',
                      'created_at', 'domain_name', 'role')
        if email is None:
            query = textwrap.dedent('''\
                query {
                    user {$fields}
                }
            ''')
        else:
            query = textwrap.dedent('''\
                query($email: String) {
                    user(email: $email) {$fields}
                }
            ''')
        query = query.replace('$fields', ' '.join(fields))
        variables = {'email': email}
        rqst = Request(cls.session, 'POST', '/admin/graphql')
        if email is None:
            rqst.set_json({
                'query': query,
            })
        else:
            rqst.set_json({
                'query': query,
                'variables': variables,
            })
        async with rqst.fetch() as resp:
            data = await resp.json()
            return data['user']

    @api_function
    @classmethod
    async def detail_by_uuid(cls, user_uuid: str = None, fields: Iterable[str] = None) -> Sequence[dict]:
        '''
        Fetch information of a user by user's uuid. If user_uuid is not specified,
        requester's information will be returned.

        :param user_uuid: UUID of the user to fetch.
        :param fields: Additional per-user query fields to fetch.
        '''
        if fields is None:
            fields = ('uuid', 'username', 'email', 'need_password_change', 'is_active',
                      'created_at', 'domain_name', 'role')
        if user_uuid is None:
            query = textwrap.dedent('''\
                query {
                    user {$fields}
                }
            ''')
        else:
            query = textwrap.dedent('''\
                query($user_id: String) {
                    user_from_uuid(user_id: $user_id) {$fields}
                }
            ''')
        query = query.replace('$fields', ' '.join(fields))
        variables = {'user_id': user_uuid}
        rqst = Request(cls.session, 'POST', '/admin/graphql')
        if user_uuid is None:
            rqst.set_json({
                'query': query,
            })
        else:
            rqst.set_json({
                'query': query,
                'variables': variables,
            })
        async with rqst.fetch() as resp:
            data = await resp.json()
            return data['user_from_uuid']

    @api_function
    @classmethod
    async def create(cls, domain_name: str, email: str, password: str,
                     username: str = None, full_name: str = None,
                     role: str = 'user', is_active: bool = True,
                     need_password_change: bool = False,
                     description: str = '',
                     group_ids: Iterable[str] = None,
                     fields: Iterable[str] = None) -> dict:
        '''
        Creates a new user with the given options.
        You need an admin privilege for this operation.
        '''
        if fields is None:
            fields = ('domain_name', 'email', 'username',)
        query = textwrap.dedent('''\
            mutation($email: String!, $input: UserInput!) {
                create_user(email: $email, props: $input) {
                    ok msg user {$fields}
                }
            }
        ''')
        query = query.replace('$fields', ' '.join(fields))
        variables = {
            'email': email,
            'input': {
                'password': password,
                'username': username,
                'full_name': full_name,
                'role': role,
                'is_active': is_active,
                'need_password_change': need_password_change,
                'description': description,
                'domain_name': domain_name,
                'group_ids': group_ids,
            },
        }
        rqst = Request(cls.session, 'POST', '/admin/graphql')
        rqst.set_json({
            'query': query,
            'variables': variables,
        })
        async with rqst.fetch() as resp:
            data = await resp.json()
            return data['create_user']

    @api_function
    @classmethod
    async def update(cls, email: str, password: str = None, username: str = None,
                     full_name: str = None, domain_name: str = None, role: str = None,
                     is_active: bool = None, need_password_change: bool = None,
                     description: str = None, group_ids: Iterable[str] = None,
                     fields: Iterable[str] = None) -> dict:
        '''
        Update existing user.
        You need an admin privilege for this operation.
        '''
        query = textwrap.dedent('''\
            mutation($email: String!, $input: ModifyUserInput!) {
                modify_user(email: $email, props: $input) {
                    ok msg
                }
            }
        ''')
        variables = {
            'email': email,
            'input': {
                'password': password,
                'username': username,
                'full_name': full_name,
                'domain_name': domain_name,
                'role': role,
                'is_active': is_active,
                'need_password_change': need_password_change,
                'description': description,
                'group_ids': group_ids,
            },
        }
        rqst = Request(cls.session, 'POST', '/admin/graphql')
        rqst.set_json({
            'query': query,
            'variables': variables,
        })
        async with rqst.fetch() as resp:
            data = await resp.json()
            return data['modify_user']

    @api_function
    @classmethod
    async def delete(cls, email: str):
        '''
        Deletes an existing user.
        '''
        query = textwrap.dedent('''\
            mutation($email: String!) {
                delete_user(email: $email) {
                    ok msg
                }
            }
        ''')
        variables = {'email': email}
        rqst = Request(cls.session, 'POST', '/admin/graphql')
        rqst.set_json({
            'query': query,
            'variables': variables,
        })
        async with rqst.fetch() as resp:
            data = await resp.json()
            return data['delete_user']
