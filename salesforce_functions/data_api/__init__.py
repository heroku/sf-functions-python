from json.decoder import JSONDecodeError
from typing import TypeVar

from aiohttp import ClientSession

from ..__version__ import __version__
from .exceptions import UnexpectedRestApiResponsePayload
from .record import Record, RecordQueryResult
from .reference_id import ReferenceId
from .requests import (
    CompositeGraphRestApiRequest,
    CreateRecordRestApiRequest,
    DeleteRecordRestApiRequest,
    QueryNextRecordsRestApiRequest,
    QueryRecordsRestApiRequest,
    RestApiRequest,
    UpdateRecordRestApiRequest,
)
from .unit_of_work import UnitOfWork

T = TypeVar("T")


class DataAPI:
    """Data API client to interact with data in a Salesforce org."""

    def __init__(
        self, org_domain_url: str, api_version: str, access_token: str
    ) -> None:
        self._api_version = api_version
        self._org_domain_url = org_domain_url

        self.access_token = access_token

    async def query(self, soql: str) -> RecordQueryResult:
        """Queries for records with a given SOQL string."""

        return await self._execute(QueryRecordsRestApiRequest(soql))

    async def query_more(self, result: RecordQueryResult) -> RecordQueryResult:
        """Queries for more records, based on the given RecordQueryResult."""

        if result.next_records_url is None:
            return RecordQueryResult(True, result.total_size, [], None)

        return await self._execute(
            QueryNextRecordsRestApiRequest(result.next_records_url)
        )

    async def create(self, record: Record) -> str:
        """Create a new record based on the given Record object."""

        return await self._execute(CreateRecordRestApiRequest(record))

    async def update(self, record: Record) -> str:
        """
        Updates a new record based on the given Record object.

        The given Record must contain an "Id" field.
        """

        return await self._execute(UpdateRecordRestApiRequest(record))

    async def delete(self, object_type: str, record_id: str) -> str:
        """Deletes an existing record of the given type and id."""

        return await self._execute(DeleteRecordRestApiRequest(object_type, record_id))

    async def commit_unit_of_work(
        self, unit_of_work: UnitOfWork
    ) -> dict[ReferenceId, str]:
        """
        Commits a UnitOfWork, executing all operations registered with it.

        If any of these operations fail, the whole unit is rolled back. To examine results for a single operation,
        inspect the returned dict (which is keyed with ReferenceId objects returned from the register* functions on
        UnitOfWork).
        """
        return await self._execute(
            # pylint:disable=protected-access
            CompositeGraphRestApiRequest(
                self._org_domain_url, self._api_version, unit_of_work._sub_requests
            )
        )

    async def _execute(self, rest_api_request: RestApiRequest[T]) -> T:
        url: str = rest_api_request.url(self._org_domain_url, self._api_version)
        method: str = rest_api_request.http_method()
        body = rest_api_request.request_body()

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Sforce-Call-Options": f"client=sf-functions-python:{__version__}",
        }

        async with ClientSession() as client_session:
            response = await client_session.request(
                method, url, headers=headers, json=body
            )

            try:
                return rest_api_request.process_response(
                    response.status,
                    response.headers,
                    # Disable content type validation:
                    # https://docs.aiohttp.org/en/stable/client_advanced.html#disabling-content-type-validation-for-json-responses
                    # Some successful requests.py return 204 (No Content) which will not have an
                    # application/json content type header. However, these parse just fine as JSON helping to unify the
                    # interface to the REST request classes.
                    await response.json(content_type=None),
                )
            except JSONDecodeError as exception:
                raise UnexpectedRestApiResponsePayload() from exception
