import textwrap
from typing import Iterable, Sequence

from .base import api_function
from .request import Request

__all__ = (
    'Agent',
    'AgentWatcher',
)


class Agent:
    '''
    Provides a shortcut of :func:`Admin.query()
    <ai.backend.client.admin.Admin.query>` that fetches various agent
    information.

    .. note::

      All methods in this function class require your API access key to
      have the *admin* privilege.
    '''

    session = None
    '''The client session instance that this function class is bound to.'''

    @api_function
    @classmethod
    async def list_with_limit(cls,
                              limit,
                              offset,
                              status: str = 'ALIVE',
                              fields: Iterable[str] = None) -> Sequence[dict]:
        '''
        Fetches the list of agents with the given status with limit and offset for
        pagination.

        :param limit: number of agents to get
        :param offset: offset index of agents to get
        :param status: An upper-cased string constant representing agent
            status (one of ``'ALIVE'``, ``'TERMINATED'``, ``'LOST'``,
            etc.)
        :param fields: Additional per-agent query fields to fetch.
        '''
        if fields is None:
            fields = (
                'id',
                'addr',
                'status',
                'first_contact',
                'mem_slots',
                'cpu_slots',
                'gpu_slots',
            )
        q = 'query($limit: Int!, $offset: Int!, $status: String) {' \
            '  agent_list(limit: $limit, offset: $offset, status: $status) {' \
            '   items { $fields }' \
            '   total_count' \
            '  }' \
            '}'
        q = q.replace('$fields', ' '.join(fields))
        variables = {
            'limit': limit,
            'offset': offset,
            'status': status,
        }
        rqst = Request(cls.session, 'POST', '/admin/graphql')
        rqst.set_json({
            'query': q,
            'variables': variables,
        })
        async with rqst.fetch() as resp:
            data = await resp.json()
            return data['agent_list']

    @api_function
    @classmethod
    async def detail(cls, agent_id: str, fields: Iterable[str] = None) -> Sequence[dict]:
        if fields is None:
            fields = ('id', 'status', 'addr', 'region', 'first_contact',
                      'cpu_cur_pct', 'mem_cur_bytes',
                      'available_slots', 'occupied_slots')
        query = textwrap.dedent('''\
            query($agent_id: String!) {
                agent(agent_id: $agent_id) {$fields}
            }
        ''')
        query = query.replace('$fields', ' '.join(fields))
        variables = {'agent_id': agent_id}
        rqst = Request(cls.session, 'POST', '/admin/graphql')
        rqst.set_json({
            'query': query,
            'variables': variables,
        })
        async with rqst.fetch() as resp:
            data = await resp.json()
            return data['agent']


class AgentWatcher:
    '''
    Provides a shortcut of :func:`Admin.query()
    <ai.backend.client.admin.Admin.query>` that manipulate agent status.

    .. note::

      All methods in this function class require you to
      have the *superadmin* privilege.
    '''

    session = None
    '''The client session instance that this function class is bound to.'''

    @api_function
    @classmethod
    async def get_status(cls, agent_id: str) -> dict:
        '''
        Get agent and watcher status.
        '''
        rqst = Request(cls.session, 'GET', '/resource/watcher')
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
        '''
        Start agent.
        '''
        rqst = Request(cls.session, 'POST', '/resource/watcher/agent/start')
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
        '''
        Stop agent.
        '''
        rqst = Request(cls.session, 'POST', '/resource/watcher/agent/stop')
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
        '''
        Restart agent.
        '''
        rqst = Request(cls.session, 'POST', '/resource/watcher/agent/restart')
        rqst.set_json({'agent_id': agent_id})
        async with rqst.fetch() as resp:
            data = await resp.json()
            if 'message' in data:
                return data['message']
            else:
                return data
