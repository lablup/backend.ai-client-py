import textwrap
from typing import Iterable, Sequence

from .base import api_function, BaseFunction
from ..session import api_session

__all__ = (
    'Domain',
)


class Domain(BaseFunction):
    """
    Provides a shortcut of :func:`Admin.query()
    <ai.backend.client.admin.Admin.query>` that fetches various domain
    information.

    .. note::

      All methods in this function class require your API access key to
      have the *admin* privilege.
    """

    @api_function
    @classmethod
    async def list(cls, fields: Iterable[str] = None) -> Sequence[dict]:
        """
        Fetches the list of domains.

        :param fields: Additional per-domain query fields to fetch.
        """
        if fields is None:
            fields = ('name', 'description', 'is_active', 'created_at',
                      'total_resource_slots', 'allowed_vfolder_hosts', 'allowed_docker_registries',
                      'integration_id')
        query = textwrap.dedent("""\
            query {
                domains {$fields}
            }
        """)
        query = query.replace('$fields', ' '.join(fields))
        data = await api_session.get().Admin._query(query)
        return data['domains']

    @api_function
    @classmethod
    async def detail(cls, name: str, fields: Iterable[str] = None) -> Sequence[dict]:
        """
        Fetch information of a domain with name.

        :param name: Name of the domain to fetch.
        :param fields: Additional per-domain query fields to fetch.
        """
        if fields is None:
            fields = ('name', 'description', 'is_active', 'created_at',
                      'total_resource_slots', 'allowed_vfolder_hosts', 'allowed_docker_registries',
                      'integration_id',)
        query = textwrap.dedent("""\
            query($name: String) {
                domain(name: $name) {$fields}
            }
        """)
        query = query.replace('$fields', ' '.join(fields))
        variables = {'name': name}
        data = await api_session.get().Admin._query(query, variables)
        return data['domain']

    @api_function
    @classmethod
    async def create(cls, name: str, description: str = '', is_active: bool = True,
                     total_resource_slots: str = None,
                     allowed_vfolder_hosts: Iterable[str] = None,
                     allowed_docker_registries: Iterable[str] = None,
                     integration_id: str = None,
                     fields: Iterable[str] = None) -> dict:
        """
        Creates a new domain with the given options.
        You need an admin privilege for this operation.
        """
        if fields is None:
            fields = ('name',)
        query = textwrap.dedent("""\
            mutation($name: String!, $input: DomainInput!) {
                create_domain(name: $name, props: $input) {
                    ok msg domain {$fields}
                }
            }
        """)
        query = query.replace('$fields', ' '.join(fields))
        variables = {
            'name': name,
            'input': {
                'description': description,
                'is_active': is_active,
                'total_resource_slots': total_resource_slots,
                'allowed_vfolder_hosts': allowed_vfolder_hosts,
                'allowed_docker_registries': allowed_docker_registries,
                'integration_id': integration_id,
            },
        }
        data = await api_session.get().Admin._query(query, variables)
        return data['create_domain']

    @api_function
    @classmethod
    async def update(cls, name: str, new_name: str = None, description: str = None,
                     is_active: bool = None, total_resource_slots: str = None,
                     allowed_vfolder_hosts: Iterable[str] = None,
                     allowed_docker_registries: Iterable[str] = None,
                     integration_id: str = None,
                     fields: Iterable[str] = None) -> dict:
        """
        Update existing domain.
        You need an admin privilege for this operation.
        """
        query = textwrap.dedent("""\
            mutation($name: String!, $input: ModifyDomainInput!) {
                modify_domain(name: $name, props: $input) {
                    ok msg
                }
            }
        """)
        variables = {
            'name': name,
            'input': {
                'name': new_name,
                'description': description,
                'is_active': is_active,
                'total_resource_slots': total_resource_slots,
                'allowed_vfolder_hosts': allowed_vfolder_hosts,
                'allowed_docker_registries': allowed_docker_registries,
                'integration_id': integration_id,
            },
        }
        data = await api_session.get().Admin._query(query, variables)
        return data['modify_domain']

    @api_function
    @classmethod
    async def delete(cls, name: str):
        """
        Inactivates an existing domain.
        """
        query = textwrap.dedent("""\
            mutation($name: String!) {
                delete_domain(name: $name) {
                    ok msg
                }
            }
        """)
        variables = {'name': name}
        data = await api_session.get().Admin._query(query, variables)
        return data['delete_domain']

    @api_function
    @classmethod
    async def purge(cls, name: str):
        """
        Deletes an existing domain.
        """
        query = textwrap.dedent("""\
            mutation($name: String!) {
                purge_domain(name: $name) {
                    ok msg
                }
            }
        """)
        variables = {'name': name}
        data = await api_session.get().Admin._query(query, variables)
        return data['purge_domain']
