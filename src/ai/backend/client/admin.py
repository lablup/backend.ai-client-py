from typing import Any, Mapping, Optional

from .base import BaseFunction, SyncFunctionMixin
from .request import Request

__all__ = (
    'BaseAdmin',
    'Admin',
)


class BaseAdmin(BaseFunction):

    _session = None

    @classmethod
    def _query(cls, query: str,
               variables: Optional[Mapping[str, Any]] = None):
        gql_query = {
            'query': query,
            'variables': variables if variables else {},
        }
        resp = yield Request(cls._session,
                             'POST', '/admin/graphql',
                             gql_query)
        return resp.json()

    def __init_subclass__(cls):
        cls.query = cls._call_base_clsmethod(cls._query)


class Admin(SyncFunctionMixin, BaseAdmin):
    '''
    Deprecated! Use ai.backend.client.Session instead.
    '''
    pass
