from dataclasses import dataclass
from typing import Any, Literal, Mapping

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
    next_records_url: str | None
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
        org_domain_url: str,
        api_version: str,
        access_token: str,
        # TODO: Should we try and prevent this type from leaking into public API?
        session: ClientSession,
    ):
        self.org_domain_url = org_domain_url
        self.api_version = api_version
        self.access_token = access_token
        self._session = session

    async def query(self, soql: str) -> RecordQueryResult:
        """Queries for records with the given SOQL string."""
        raise NotImplementedError

        # pylint: disable-next=unreachable
        result = await self._request(
            "GET",
            f"{self.org_domain_url}/services/data/v{self.api_version}/query/",
            params={"q": soql},
        )
        return result

    async def _request(
        self,
        method: Literal["GET", "POST", "PATCH", "DELETE"],
        url: str,
        params: Mapping[str, str] | None = None,
        json: Any | None = None,
    ) -> Any:
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
        result = await response.json()
        return result

    async def query_more(
        self, record_query_result: RecordQueryResult
    ) -> RecordQueryResult:
        """Queries for more records, based on the given `RecordQueryResult`."""
        raise NotImplementedError

    async def create(self, record: Record) -> RecordModificationResult:
        """Creates a new record described by the given `Record`."""
        raise NotImplementedError

    async def update(self, record: Record) -> RecordModificationResult:
        """Updates an existing record described by the given `Record`."""
        raise NotImplementedError

    async def delete(
        self, record_type: str, record_id: str
    ) -> RecordModificationResult:
        """Deletes a record, based on the given type and id."""
        raise NotImplementedError
