from dataclasses import dataclass
from typing import Any, Literal, Mapping, Optional

from aiohttp import ClientSession

from .__version__ import __version__


@dataclass(frozen=True, slots=True)
class Record:
    """A Salesforce record."""

    type: str
    """The Salesforce Object type."""
    fields: dict[str, Any]
    """The fields belonging to the record."""


@dataclass(frozen=True, slots=True)
class RecordQueryResult:
    """The result of a record query."""

    done: bool
    """
    Indicates whether all record results have been returned.

    If true, no additional records can be retrieved from the query result.
    If false, one or more records remain to be retrieved.
    """
    total_size: int
    """
    The total number of records returned by the query.

    This is not necessarily the same number of records found in `records`.
    """
    records: list[dict[str, Any]]
    """
    The `Record`s in this query result.

    Use `done` to determine whether there are additional records to be
    queried with `queryMore`.
    """
    next_records_url: Optional[str]
    """The URL for the next set of records, if any."""


@dataclass(frozen=True, slots=True)
class RecordModificationResult:
    """The result of a record modification such as a create, update or delete."""

    id: str
    """The ID of the modified record."""


class RestAPIException(Exception):
    pass


class DataAPI:
    def __init__(
        self,
        salesforce_base_url: str,
        api_version: str,
        access_token: str,
        # TODO: Should we try and prevent this type from leaking into public API?
        session: ClientSession,
    ):
        self.salesforce_base_url = salesforce_base_url
        self.api_version = api_version
        self.access_token = access_token
        self._session = session

    async def query(self, soql: str) -> RecordQueryResult:
        """Queries for records with the given SOQL string."""
        result = await self._request(
            "GET",
            f"{self.salesforce_base_url}/services/data/v{self.api_version}/query/",
            params={"q": soql},
        )
        return result

    async def _request(
        self,
        method: Literal["GET", "POST", "PATCH", "DELETE"],
        url: str,
        params: Optional[Mapping[str, str]] = None,
        json: Optional[Any] = None,
    ):
        # TODO: Set `timeout=N` here? (Default is 5 mins)
        # TODO: Handle failure modes:
        # cannot connect / timeout
        # HTTP 5xx
        # HTTP 4xx
        # HTTP 3xx
        # Not valid JSON
        # [{"message":"A query string has to be specified","errorCode":"MALFORMED_QUERY"}]
        # [{"message":"SOQL statements cannot be empty or null","errorCode":"MALFORMED_QUERY"}]
        # [{"message":"INVALID_HEADER_TYPE","errorCode":"INVALID_AUTH_HEADER"}]
        # [{"message":"Session expired or invalid","errorCode":"INVALID_SESSION_ID"}]
        # [{"errorCode":"NOT_FOUND","message":"The requested resource does not exist"}]

        response = await self._session.request(
            method,
            url,
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Sforce-Call-Options": f"client=sf-functions-python:{__version__}",
            },
            params=params,
            json=json,
        )
        # response.raise_for_status()
        result = await response.text()
        return result

    # async def queryMore(
    #     self, record_query_result: RecordQueryResult
    # ) -> RecordQueryResult:
    #     """Queries for more records, based on the given `RecordQueryResult`."""
    #     pass

    # async def create(self, record: Record) -> RecordModificationResult:
    #     """Creates a new record described by the given `Record`."""
    #     pass

    # async def update(self, record: Record) -> RecordModificationResult:
    #     """Updates an existing record described by the given `Record`."""
    #     pass

    # async def delete(self, type: str, id: str) -> RecordModificationResult:
    #     """Deletes a record, based on the given type and id."""
    #     pass


# {
#   "totalSize": 7,
#   "done": true,
#   "records": [
#     {
#       "attributes": {
#         "type": "User",
#         "url": "/services/data/v55.0/sobjects/User/0058d000003ZO8yAAG"
#       },
#       "Name": "Ed Morley"
#     },
#     {
#       "attributes": {
#         "type": "User",
#         "url": "/services/data/v55.0/sobjects/User/0058d0000048TBKAA2"
#       },
#       "Name": "Chatter Expert"
#     }
#   ]
# }
