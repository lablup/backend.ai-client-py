from typing import Any, Mapping, Optional

from .base import api_function
from .request import Request

__all__ = (
    'Admin',
)


class Admin:

    session = None

    @api_function
    @classmethod
    async def query(cls, query: str,
                    variables: Optional[Mapping[str, Any]] = None):
        gql_query = {
            'query': query,
            'variables': variables if variables else {},
        }
        rqst = Request(cls.session, 'POST', '/admin/graphql')
        rqst.set_json(gql_query)
        async with rqst.fetch() as resp:
            return await resp.json()
