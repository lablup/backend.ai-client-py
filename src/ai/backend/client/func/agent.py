import textwrap
from typing import (
    AsyncIterator,
    Sequence,
)

from .base import api_function, BaseFunction
from ..request import Request
from ..session import api_session
from ..pagination import generate_paginated_results

__all__ = (
    'Agent',
    'AgentWatcher',
)

_default_list_fields = (
    'id',
    'status',
    'scaling_group',
    'available_slots',
    'occupied_slots',
)

_default_detail_fields = (
    'id',
    'status',
    'scaling_group',
    'addr',
    'region',
    'first_contact',
    'cpu_cur_pct',
    'mem_cur_bytes',
    'available_slots',
    'occupied_slots',
)


class Agent(BaseFunction):
    """
    Provides a shortcut of :func:`Admin.query()
    <ai.backend.client.admin.Admin.query>` that fetches various agent
    information.

    .. note::

      All methods in this function class require your API access key to
      have the *admin* privilege.
    """

    @api_function
    @classmethod
    async def paginated_list(
        cls,
        status: str = 'ALIVE',
        scaling_group: str = None,
        *,
        fields: Sequence[str] = _default_list_fields,
        page_size: int = 20,
        filter: str = None,
        order: str = None,
    ) -> AsyncIterator[dict]:
        """
        Lists the keypairs.
        You need an admin privilege for this operation.
        """
        async for item in generate_paginated_results(
            'agent_list',
            {
                'status': (status, 'String'),
                'scaling_group': (scaling_group, 'String'),
                'filter': (filter, 'String'),
                'order': (order, 'String'),
            },
            fields,
            page_size=page_size,
        ):
            yield item

    @api_function
    @classmethod
    async def detail(
        cls,
        agent_id: str,
        fields: Sequence[str] = _default_detail_fields,
    ) -> Sequence[dict]:
        query = textwrap.dedent("""\
            query($agent_id: String!) {
                agent(agent_id: $agent_id) {$fields}
            }
        """)
        query = query.replace('$fields', ' '.join(fields))
        variables = {'agent_id': agent_id}
        data = await api_session.get().Admin._query(query, variables)
        return data['agent']


class AgentWatcher(BaseFunction):
    """
    Provides a shortcut of :func:`Admin.query()
    <ai.backend.client.admin.Admin.query>` that manipulate agent status.

    .. note::

      All methods in this function class require you to
      have the *superadmin* privilege.
    """

    @api_function
    @classmethod
    async def get_status(cls, agent_id: str) -> dict:
        """
        Get agent and watcher status.
        """
        rqst = Request('GET', '/resource/watcher')
        rqst.set_json({'agent_id': agent_id})
        async with rqst.fetch() as resp:
            data = await resp.json()
            if 'message' in data:
                return data['message']
            else:
                return data

    @api_function
    @classmethod
    async def agent_start(cls, agent_id: str) -> dict:
        """
        Start agent.
        """
        rqst = Request('POST', '/resource/watcher/agent/start')
        rqst.set_json({'agent_id': agent_id})
        async with rqst.fetch() as resp:
            data = await resp.json()
            if 'message' in data:
                return data['message']
            else:
                return data

    @api_function
    @classmethod
    async def agent_stop(cls, agent_id: str) -> dict:
        """
        Stop agent.
        """
        rqst = Request('POST', '/resource/watcher/agent/stop')
        rqst.set_json({'agent_id': agent_id})
        async with rqst.fetch() as resp:
            data = await resp.json()
            if 'message' in data:
                return data['message']
            else:
                return data

    @api_function
    @classmethod
    async def agent_restart(cls, agent_id: str) -> dict:
        """
        Restart agent.
        """
        rqst = Request('POST', '/resource/watcher/agent/restart')
        rqst.set_json({'agent_id': agent_id})
        async with rqst.fetch() as resp:
            data = await resp.json()
            if 'message' in data:
                return data['message']
            else:
                return data
