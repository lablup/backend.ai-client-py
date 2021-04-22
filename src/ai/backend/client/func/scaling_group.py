import json
import textwrap
from typing import Iterable, Mapping, Sequence

from .base import api_function, BaseFunction
from ..request import Request

__all__ = (
    'ScalingGroup',
)


class ScalingGroup(BaseFunction):
    """
    Provides getting scaling-group information required for the current user.

    The scaling-group is an opaque server-side configuration which splits the whole
    cluster into several partitions, so that server administrators can apply different auto-scaling
    policies and operation standards to each partition of agent sets.
    """

    def __init__(self, name: str):
        self.name = name

    @api_function
    @classmethod
    async def list_available(cls, group: str):
        """
        List available scaling groups for the current user,
        considering the user, the user's domain, and the designated user group.
        """
        rqst = Request('GET', '/scaling-groups',
                       params={'group': group})
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def list(cls, fields: Iterable[str] = None) -> Sequence[dict]:
        """
        List available scaling groups for the current user,
        considering the user, the user's domain, and the designated user group.
        """
        if fields is None:
            fields = ('name', 'description', 'is_active',
                      'created_at',
                      'driver', 'driver_opts',
                      'scheduler', 'scheduler_opts',)
        query = textwrap.dedent("""\
            query($is_active: Boolean) {
                scaling_groups(is_active: $is_active) {
                    $fields
                }
            }
        """)
        query = query.replace('$fields', ' '.join(fields))
        variables = {'is_active': None}
        rqst = Request('POST', '/admin/graphql')
        rqst.set_json({
            'query': query,
            'variables': variables
        })
        async with rqst.fetch() as resp:
            data = await resp.json()
            return data['scaling_groups']

    @api_function
    @classmethod
    async def detail(cls, name: str, fields: Iterable[str] = None) -> Sequence[dict]:
        """
        Fetch information of a scaling group by name.

        :param name: Name of the scaling group.
        :param fields: Additional per-scaling-group query fields.
        """
        if fields is None:
            fields = ('name', 'description', 'is_active',
                      'created_at',
                      'driver', 'driver_opts',
                      'scheduler', 'scheduler_opts',)
        query = textwrap.dedent("""\
            query($name: String) {
                scaling_group(name: $name) {$fields}
            }
        """)
        query = query.replace('$fields', ' '.join(fields))
        variables = {'name': name}
        rqst = Request('POST', '/admin/graphql')
        rqst.set_json({
            'query': query,
            'variables': variables,
        })
        async with rqst.fetch() as resp:
            data = await resp.json()
            return data['scaling_group']

    @api_function
    @classmethod
    async def create(cls, name: str, description: str = '', is_active: bool = True,
                     driver: str = None, driver_opts: Mapping[str, str] = None,
                     scheduler: str = None, scheduler_opts: Mapping[str, str] = None,
                     fields: Iterable[str] = None) -> dict:
        """
        Creates a new scaling group with the given options.
        """
        if fields is None:
            fields = ('name',)
        query = textwrap.dedent("""\
            mutation($name: String!, $input: CreateScalingGroupInput!) {
                create_scaling_group(name: $name, props: $input) {
                    ok msg scaling_group {$fields}
                }
            }
        """)
        query = query.replace('$fields', ' '.join(fields))
        variables = {
            'name': name,
            'input': {
                'description': description,
                'is_active': is_active,
                'driver': driver,
                'driver_opts': json.dumps(driver_opts),
                'scheduler': scheduler,
                'scheduler_opts': json.dumps(scheduler_opts),
            },
        }
        rqst = Request('POST', '/admin/graphql')
        rqst.set_json({
            'query': query,
            'variables': variables,
        })
        async with rqst.fetch() as resp:
            data = await resp.json()
            return data['create_scaling_group']

    @api_function
    @classmethod
    async def update(cls, name: str, description: str = '', is_active: bool = True,
                     driver: str = None, driver_opts: Mapping[str, str] = None,
                     scheduler: str = None, scheduler_opts: Mapping[str, str] = None,
                     fields: Iterable[str] = None) -> dict:
        """
        Update existing scaling group.
        """
        if fields is None:
            fields = ('name',)
        query = textwrap.dedent("""\
            mutation($name: String!, $input: ModifyScalingGroupInput!) {
                modify_scaling_group(name: $name, props: $input) {
                    ok msg
                }
            }
        """)
        query = query.replace('$fields', ' '.join(fields))
        variables = {
            'name': name,
            'input': {
                'description': description,
                'is_active': is_active,
                'driver': driver,
                'driver_opts': json.dumps(driver_opts),
                'scheduler': scheduler,
                'scheduler_opts': json.dumps(scheduler_opts),
            },
        }
        rqst = Request('POST', '/admin/graphql')
        rqst.set_json({
            'query': query,
            'variables': variables,
        })
        async with rqst.fetch() as resp:
            data = await resp.json()
            return data['modify_scaling_group']

    @api_function
    @classmethod
    async def delete(cls, name: str):
        """
        Deletes an existing scaling group.
        """
        query = textwrap.dedent("""\
            mutation($name: String!) {
                delete_scaling_group(name: $name) {
                    ok msg
                }
            }
        """)
        variables = {'name': name}
        rqst = Request('POST', '/admin/graphql')
        rqst.set_json({
            'query': query,
            'variables': variables,
        })
        async with rqst.fetch() as resp:
            data = await resp.json()
            return data['delete_scaling_group']

    @api_function
    @classmethod
    async def associate_domain(cls, scaling_group: str, domain: str):
        """
        Associate scaling_group with domain.

        :param scaling_group: The name of a scaling group.
        :param domain: The name of a domain.
        """
        query = textwrap.dedent("""\
            mutation($scaling_group: String!, $domain: String!) {
                associate_scaling_group_with_domain(
                        scaling_group: $scaling_group, domain: $domain) {
                    ok msg
                }
            }
        """)
        variables = {'scaling_group': scaling_group, 'domain': domain}
        rqst = Request('POST', '/admin/graphql')
        rqst.set_json({
            'query': query,
            'variables': variables,
        })
        async with rqst.fetch() as resp:
            data = await resp.json()
            return data['associate_scaling_group_with_domain']

    @api_function
    @classmethod
    async def dissociate_domain(cls, scaling_group: str, domain: str):
        """
        Dissociate scaling_group from domain.

        :param scaling_group: The name of a scaling group.
        :param domain: The name of a domain.
        """
        query = textwrap.dedent("""\
            mutation($scaling_group: String!, $domain: String!) {
                disassociate_scaling_group_with_domain(
                        scaling_group: $scaling_group, domain: $domain) {
                    ok msg
                }
            }
        """)
        variables = {'scaling_group': scaling_group, 'domain': domain}
        rqst = Request('POST', '/admin/graphql')
        rqst.set_json({
            'query': query,
            'variables': variables,
        })
        async with rqst.fetch() as resp:
            data = await resp.json()
            return data['disassociate_scaling_group_with_domain']

    @api_function
    @classmethod
    async def dissociate_all_domain(cls, domain: str):
        """
        Dissociate all scaling_groups from domain.

        :param domain: The name of a domain.
        """
        query = textwrap.dedent("""\
            mutation($domain: String!) {
                disassociate_all_scaling_groups_with_domain(domain: $domain) {
                    ok msg
                }
            }
        """)
        variables = {'domain': domain}
        rqst = Request('POST', '/admin/graphql')
        rqst.set_json({
            'query': query,
            'variables': variables,
        })
        async with rqst.fetch() as resp:
            data = await resp.json()
            return data['disassociate_all_scaling_groups_with_domain']

    @api_function
    @classmethod
    async def associate_group(cls, scaling_group: str, group_id: str):
        """
        Associate scaling_group with group.

        :param scaling_group: The name of a scaling group.
        :param group_id: The ID of a group.
        """
        query = textwrap.dedent("""\
            mutation($scaling_group: String!, $user_group: UUID!) {
                associate_scaling_group_with_user_group(
                        scaling_group: $scaling_group, user_group: $user_group) {
                    ok msg
                }
            }
        """)
        variables = {'scaling_group': scaling_group, 'user_group': group_id}
        rqst = Request('POST', '/admin/graphql')
        rqst.set_json({
            'query': query,
            'variables': variables,
        })
        async with rqst.fetch() as resp:
            data = await resp.json()
            return data['associate_scaling_group_with_user_group']

    @api_function
    @classmethod
    async def dissociate_group(cls, scaling_group: str, group_id: str):
        """
        Dissociate scaling_group from group.

        :param scaling_group: The name of a scaling group.
        :param group_id: The ID of a group.
        """
        query = textwrap.dedent("""\
            mutation($scaling_group: String!, $user_group: String!) {
                disassociate_scaling_group_with_user_group(
                        scaling_group: $scaling_group, user_group: $user_group) {
                    ok msg
                }
            }
        """)
        variables = {'scaling_group': scaling_group, 'user_group': group_id}
        rqst = Request('POST', '/admin/graphql')
        rqst.set_json({
            'query': query,
            'variables': variables,
        })
        async with rqst.fetch() as resp:
            data = await resp.json()
            return data['disassociate_scaling_group_with_user_group']

    @api_function
    @classmethod
    async def dissociate_all_group(cls, group_id: str):
        """
        Dissociate all scaling_groups from group.

        :param group_id: The ID of a group.
        """
        query = textwrap.dedent("""\
            mutation($group_id: UUID!) {
                disassociate_all_scaling_groups_with_group(user_group: $group_id) {
                    ok msg
                }
            }
        """)
        variables = {'group_id': group_id}
        rqst = Request('POST', '/admin/graphql')
        rqst.set_json({
            'query': query,
            'variables': variables,
        })
        async with rqst.fetch() as resp:
            data = await resp.json()
            return data['disassociate_all_scaling_groups_with_group']
