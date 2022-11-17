from typing import Any, Literal, Mapping

from aiohttp import ClientSession

from ..__version__ import __version__
from .record import Record, RecordModificationResult, RecordQueryResult


class DataAPI:
    def __init__(
        self,
        api_version: str,
        org_domain_url: str,
        access_token: str,
        session: ClientSession | None = None,
    ):
        self._api_version = api_version
        self._org_domain_url = org_domain_url
        self._shared_session = session

        self.access_token = access_token

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

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Sforce-Call-Options": f"client=sf-functions-python:{__version__}",
        }

        session = self._shared_session or ClientSession()

        try:
            response = await session.request(
                method,
                url,
                headers=headers,
                params=params,
                json=json,
            )
            # response.raise_for_status()
            result = await response.json()
        finally:
            if not self._shared_session:
                await session.close()

        return result
