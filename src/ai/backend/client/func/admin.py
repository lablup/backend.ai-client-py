from typing import Any, Mapping, Optional

from .base import api_function, BaseFunction
from ..request import Request

__all__ = (
    'Admin',
)


class Admin(BaseFunction):
    """
    Provides the function interface for making admin GrapQL queries.

    .. note::

      Depending on the privilege of your API access key, you may or may not
      have access to querying/mutating server-side resources of other
      users.
    """

    @api_function
    @classmethod
    async def query(
        cls, query: str,
        variables: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        """
        Sends the GraphQL query and returns the response.

        :param query: The GraphQL query string.
        :param variables: An optional key-value dictionary
            to fill the interpolated template variables
            in the query.

        :returns: The object parsed from the response JSON string.
        """
        gql_query = {
            'query': query,
            'variables': variables if variables else {},
        }
        rqst = Request('POST', '/admin/graphql')
        rqst.set_json(gql_query)
        async with rqst.fetch() as resp:
            return await resp.json()
