from typing import Optional, Iterable

from .base import api_function
from .request import Request

__all__ = (
    'Agent',
)


class Agent:

    session = None

    @api_function
    @classmethod
    async def list(cls,
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
        variables = {
            'status': status,
        }
        rqst = Request(cls.session, 'POST', '/admin/graphql')
        rqst.set_json({
            'query': q,
            'variables': variables,
        })
        async with rqst.fetch() as resp:
            data = await resp.json()
            return data['agents']
