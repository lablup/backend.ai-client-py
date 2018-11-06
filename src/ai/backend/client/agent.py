from typing import Optional, Iterable

from .base import BaseFunction, SyncFunctionMixin
from .request import Request

__all__ = (
    'BaseAgent',
    'Agent',
)


class BaseAgent(BaseFunction):

    _session = None

    @classmethod
    def _list(cls,
              status: str = 'ALIVE',
              fields: Optional[Iterable[str]] = None):
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
        q = 'query($status: String) {' \
            '  agents(status: $status) {' \
            '    $fields' \
            '  }' \
            '}'
        q = q.replace('$fields', ' '.join(fields))
        vars = {
            'status': status,
        }
        resp = yield Request(cls._session,
            'POST', '/admin/graphql', {
                'query': q,
                'variables': vars,
            })
        data = resp.json()
        return data['agents']

    def __init_subclass__(cls):
        cls.list = cls._call_base_clsmethod(cls._list)


class Agent(SyncFunctionMixin, BaseAgent):
    '''
    Deprecated! Use ai.backend.client.Session instead.
    '''
    pass
