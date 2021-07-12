from typing import Iterable, Sequence

from .base import api_function, BaseFunction
from ..session import api_session

__all__ = (
    'KeypairResourcePolicy'
)


class KeypairResourcePolicy(BaseFunction):
    """
    Provides interactions with keypair resource policy.
    """

    def __init__(self, access_key: str):
        self.access_key = access_key

    @api_function
    @classmethod
    async def create(cls, name: str,
                     default_for_unspecified: int,
                     total_resource_slots: int,
                     max_concurrent_sessions: int,
                     max_containers_per_session: int,
                     max_vfolder_count: int,
                     max_vfolder_size: int,
                     idle_timeout: int,
                     allowed_vfolder_hosts: Sequence[str],
                     fields: Iterable[str] = None) -> dict:
        """
        Creates a new keypair resource policy with the given options.
        You need an admin privilege for this operation.
        """
        if fields is None:
            fields = ('name',)
        q = 'mutation($name: String!, $input: CreateKeyPairResourcePolicyInput!) {' \
            + \
            '  create_keypair_resource_policy(name: $name, props: $input) {' \
            '    ok msg resource_policy { $fields }' \
            '  }' \
            '}'
        q = q.replace('$fields', ' '.join(fields))
        variables = {
            'name': name,
            'input': {
                'default_for_unspecified': default_for_unspecified,
                'total_resource_slots': total_resource_slots,
                'max_concurrent_sessions': max_concurrent_sessions,
                'max_containers_per_session': max_containers_per_session,
                'max_vfolder_count': max_vfolder_count,
                'max_vfolder_size': max_vfolder_size,
                'idle_timeout': idle_timeout,
                'allowed_vfolder_hosts': allowed_vfolder_hosts,
            },
        }
        data = await api_session.get().Admin._query(q, variables)
        return data['create_keypair_resource_policy']

    @api_function
    @classmethod
    async def update(cls, name: str,
                     default_for_unspecified: int,
                     total_resource_slots: int,
                     max_concurrent_sessions: int,
                     max_containers_per_session: int,
                     max_vfolder_count: int,
                     max_vfolder_size: int,
                     idle_timeout: int,
                     allowed_vfolder_hosts: Sequence[str]) -> dict:
        """
        Updates an existing keypair resource policy with the given options.
        You need an admin privilege for this operation.
        """
        q = 'mutation($name: String!, $input: ModifyKeyPairResourcePolicyInput!) {' \
            + \
            '  modify_keypair_resource_policy(name: $name, props: $input) {' \
            '    ok msg' \
            '  }' \
            '}'
        variables = {
            'name': name,
            'input': {
                'default_for_unspecified': default_for_unspecified,
                'total_resource_slots': total_resource_slots,
                'max_concurrent_sessions': max_concurrent_sessions,
                'max_containers_per_session': max_containers_per_session,
                'max_vfolder_count': max_vfolder_count,
                'max_vfolder_size': max_vfolder_size,
                'idle_timeout': idle_timeout,
                'allowed_vfolder_hosts': allowed_vfolder_hosts,
            },
        }
        data = await api_session.get().Admin._query(q, variables)
        return data['modify_keypair_resource_policy']

    @api_function
    @classmethod
    async def delete(cls, name: str) -> dict:
        """
        Deletes an existing keypair resource policy with given name.
        You need an admin privilege for this operation.
        """
        q = 'mutation($name: String!) {' \
            + \
            '  delete_keypair_resource_policy(name: $name) {' \
            '    ok msg' \
            '  }' \
            '}'
        variables = {
            'name': name,
        }
        data = await api_session.get().Admin._query(q, variables)
        return data['delete_keypair_resource_policy']

    @api_function
    @classmethod
    async def list(cls, fields: Iterable[str] = None) -> Sequence[dict]:
        '''
        Lists the keypair resource policies.
        You need an admin privilege for this operation.
        '''
        if fields is None:
            fields = (
                'name', 'created_at',
                'total_resource_slots', 'max_concurrent_sessions',
                'max_vfolder_count', 'max_vfolder_size',
                'idle_timeout',
            )
        q = 'query {' \
            '  keypair_resource_policies {' \
            '    $fields' \
            '  }' \
            '}'
        q = q.replace('$fields', ' '.join(fields))
        data = await api_session.get().Admin._query(q)
        return data['keypair_resource_policies']

    @api_function
    async def info(self, name: str, fields: Iterable[str] = None) -> dict:
        """
        Returns the resource policy's information.

        :param fields: Additional per-agent query fields to fetch.

        .. versionadded:: 19.03
        """
        if fields is None:
            fields = (
                'name', 'created_at',
                'total_resource_slots', 'max_concurrent_sessions',
                'max_vfolder_count', 'max_vfolder_size',
                'idle_timeout',
            )
        q = 'query($name: String) {' \
            '  keypair_resource_policy(name: $name) {' \
            '    $fields' \
            '  }' \
            '}'
        q = q.replace('$fields', ' '.join(fields))
        variables = {
            'name': name,
        }
        data = await api_session.get().Admin._query(q, variables)
        return data['keypair_resource_policy']
