from typing import Any, TypeVar

import orjson
from aiohttp import ClientSession, DummyCookieJar
from aiohttp.payload import BytesPayload

from ..__version__ import __version__
from ._requests import (
    CompositeGraphRestApiRequest,
    CreateRecordRestApiRequest,
    DeleteRecordRestApiRequest,
    QueryNextRecordsRestApiRequest,
    QueryRecordsRestApiRequest,
    RestApiRequest,
    UpdateRecordRestApiRequest,
)
from .exceptions import UnexpectedRestApiResponsePayload
from .record import Record, RecordQueryResult
from .reference_id import ReferenceId
from .unit_of_work import UnitOfWork

__all__ = ["DataAPI"]

T = TypeVar("T")


class DataAPI:
    """Data API client to interact with data in a Salesforce org."""

    def __init__(
        self,
        org_domain_url: str,
        api_version: str,
        access_token: str,
        session: ClientSession | None = None,
    ) -> None:
        self._api_version = api_version
        self._org_domain_url = org_domain_url
        self._shared_session = session

        self.access_token = access_token

    async def query(self, soql: str) -> RecordQueryResult:
        """Query for records using the given SOQL string."""
        return await self._execute(
            QueryRecordsRestApiRequest(soql, self._download_file)
        )

    async def query_more(self, result: RecordQueryResult) -> RecordQueryResult:
        """Query for more records, based on the given `RecordQueryResult`."""
        if result.next_records_url is None:
            return RecordQueryResult(True, result.total_size, [], None)

        return await self._execute(
            QueryNextRecordsRestApiRequest(result.next_records_url, self._download_file)
        )

    async def create(self, record: Record) -> str:
        """Create a new record based on the given `Record` object."""
        return await self._execute(CreateRecordRestApiRequest(record))

    async def update(self, record: Record) -> str:
        """
        Update an existing record based on the given `Record` object.

        The given `Record` must contain an `Id` field.
        """
        return await self._execute(UpdateRecordRestApiRequest(record))

    async def delete(self, object_type: str, record_id: str) -> str:
        """Deletes an existing record of the given type and id."""
        return await self._execute(DeleteRecordRestApiRequest(object_type, record_id))

    async def commit_unit_of_work(
        self, unit_of_work: UnitOfWork
    ) -> dict[ReferenceId, str]:
        """
        Commit a `UnitOfWork`, executing all operations registered with it.

        If any of these operations fail, the whole unit is rolled back. To examine results for a single operation,
        inspect the returned dict (which is keyed with `ReferenceId` objects returned from the `register*` functions on
        `UnitOfWork`).
        """
        return await self._execute(
            CompositeGraphRestApiRequest(
                self._org_domain_url,
                self._api_version,
                unit_of_work._sub_requests,  # pyright: ignore [reportPrivateUsage] pylint:disable=protected-access
            )
        )

    async def _execute(self, rest_api_request: RestApiRequest[T]) -> T:
        url: str = rest_api_request.url(self._org_domain_url, self._api_version)
        method: str = rest_api_request.http_method()
        body = rest_api_request.request_body()

        session = self._shared_session or ClientSession()

        try:
            response = await session.request(
                method,
                url,
                headers=self._default_headers(),
                data=self._json_serialize(body),
            )

            # Using orjson for faster JSON deserialization over the stdlib.
            # This is not implemented using the `loads` argument to `Response.json` since:
            # - We don't want the content type validation, since some successful requests.py return 204
            #   (No Content) which will not have an `application/json`` content type header. However,
            #   these parse just fine as JSON helping to unify the interface to the REST request classes.
            # - Orjson's performance/memory usage is better if it is passed bytes directly instead of `str`.
            response_body = await response.read()
            json_body = orjson.loads(response_body) if response_body else None
        except orjson.JSONDecodeError as e:
            raise UnexpectedRestApiResponsePayload() from e
        finally:
            if session != self._shared_session:
                await session.close()

        return await rest_api_request.process_response(response.status, json_body)

    async def _download_file(self, url: str) -> bytes:
        session = self._shared_session or self._create_session()

        try:
            response = await session.request(
                "GET", f"{self._org_domain_url}{url}", headers=self._default_headers()
            )

            return await response.read()
        finally:
            if session != self._shared_session:
                await session.close()

    def _default_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Sforce-Call-Options": f"client=sf-functions-python:{__version__}",
        }

    @staticmethod
    def _create_session() -> ClientSession:
        # Disable cookie storage using `DummyCookieJar`, given that:
        # - The same session will be used by multiple invocation events.
        # - We don't need cookie support.
        return ClientSession(cookie_jar=DummyCookieJar())

    @staticmethod
    def _json_serialize(data: Any) -> BytesPayload:
        """
        Replacement for aiohttp's default JSON implementation to use an alternative library for JSON serialisation.

        We're using `orjson` since it has much better performance than the Python stdlib's `json` module:
        https://github.com/ijl/orjson#performance

        We can't just implement this by passing `json_serialize` to `ClientSession`, due to:
        https://github.com/aio-libs/aiohttp/issues/4482

        So instead this is based on `payload.JsonPayload`:
        https://github.com/aio-libs/aiohttp/blob/v3.8.3/aiohttp/payload.py#L386-L403
        """
        return BytesPayload(
            orjson.dumps(data), content_type="utf-8", encoding="application/json"
        )
