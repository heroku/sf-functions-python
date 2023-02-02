from base64 import standard_b64encode
from typing import Any, Awaitable, Callable, Generic, Literal, TypeVar, cast
from urllib.parse import urlencode

from .exceptions import (
    InnerSalesforceRestApiError,
    MissingFieldError,
    SalesforceRestApiError,
    UnexpectedRestApiResponsePayload,
)
from .record import QueriedRecord, Record, RecordQueryResult
from .reference_id import ReferenceId

HttpMethod = Literal["GET", "POST", "PATCH", "DELETE"]
Json = dict[str, Any] | list[Any]
DownloadFileFunction = Callable[[str], Awaitable[bytes]]

T = TypeVar("T")


class RestApiRequest(Generic[T]):
    def url(self, org_domain_url: str, api_version: str) -> str:
        raise NotImplementedError  # pragma: no cover

    def http_method(self) -> HttpMethod:
        raise NotImplementedError  # pragma: no cover

    def request_body(self) -> Json | None:
        raise NotImplementedError  # pragma: no cover

    async def process_response(self, status_code: int, json_body: Json | None) -> T:
        raise NotImplementedError  # pragma: no cover


class QueryRecordsRestApiRequest(RestApiRequest[RecordQueryResult]):
    def __init__(self, soql: str, download_file_fn: DownloadFileFunction):
        self._soql = soql
        self._download_file_fn = download_file_fn

    def url(self, org_domain_url: str, api_version: str) -> str:
        return f"{org_domain_url}/services/data/v{api_version}/query?{urlencode({'q': self._soql})}"

    def http_method(self) -> HttpMethod:
        return "GET"

    def request_body(self) -> Json | None:
        return None

    async def process_response(
        self, status_code: int, json_body: Json | None
    ) -> RecordQueryResult:
        return await _process_records_response(
            status_code, json_body, self._download_file_fn
        )


class QueryNextRecordsRestApiRequest(RestApiRequest[RecordQueryResult]):
    def __init__(self, next_records_path: str, download_file_fn: DownloadFileFunction):
        self._next_records_path = next_records_path
        self._download_file_fn = download_file_fn

    def url(self, org_domain_url: str, api_version: str) -> str:
        return f"{org_domain_url}{self._next_records_path}"

    def http_method(self) -> HttpMethod:
        return "GET"

    def request_body(self) -> Json | None:
        return None

    async def process_response(
        self, status_code: int, json_body: Json | None
    ) -> RecordQueryResult:
        return await _process_records_response(
            status_code, json_body, self._download_file_fn
        )


class CreateRecordRestApiRequest(RestApiRequest[str]):
    def __init__(self, record: Record):
        self._record = record

    def url(self, org_domain_url: str, api_version: str) -> str:
        return f"{org_domain_url}/services/data/v{api_version}/sobjects/{self._record.type}"

    def http_method(self) -> HttpMethod:
        return "POST"

    def request_body(self) -> Json | None:
        return _normalize_record_fields(self._record.fields)

    async def process_response(self, status_code: int, json_body: Json | None) -> str:
        if status_code != 201:
            raise SalesforceRestApiError(api_errors=_parse_errors(json_body))

        if isinstance(json_body, dict):
            return str(json_body["id"])

        raise UnexpectedRestApiResponsePayload(
            "The create record API response payload doesn't match the expected structure."
        )  # pragma: no cover


class UpdateRecordRestApiRequest(RestApiRequest[str]):
    def __init__(self, record: Record):
        if "Id" not in record.fields:
            raise MissingFieldError(
                "The 'Id' field is required, but isn't present in the given Record."
            )

        self._record = record

    def url(self, org_domain_url: str, api_version: str) -> str:
        return f"{org_domain_url}/services/data/v{api_version}/sobjects/{self._record.type}/{self._record.fields['Id']}"

    def http_method(self) -> HttpMethod:
        return "PATCH"

    def request_body(self) -> Json | None:
        return _normalize_record_fields(
            {
                key: self._record.fields[key]
                for key in self._record.fields
                if key != "Id"
            }
        )

    async def process_response(self, status_code: int, json_body: Json | None) -> str:
        if status_code != 204:
            raise SalesforceRestApiError(
                api_errors=_parse_errors(json_body)
            )  # pragma: no cover

        return str(self._record.fields["Id"])


class DeleteRecordRestApiRequest(RestApiRequest[str]):
    def __init__(self, object_type: str, record_id: str):
        self._object_type = object_type
        self._record_id = record_id

    def url(self, org_domain_url: str, api_version: str) -> str:
        return f"{org_domain_url}/services/data/v{api_version}/sobjects/{self._object_type}/{self._record_id}"

    def http_method(self) -> HttpMethod:
        return "DELETE"

    def request_body(self) -> Json | None:
        return None

    async def process_response(self, status_code: int, json_body: Json | None) -> str:
        if status_code != 204:
            raise SalesforceRestApiError(api_errors=_parse_errors(json_body))

        return self._record_id


class CompositeGraphRestApiRequest(RestApiRequest[dict[ReferenceId, str]]):
    def __init__(
        self,
        api_version: str,
        sub_requests: dict[ReferenceId, RestApiRequest[str]],
    ):
        self._api_version = api_version
        self._sub_requests = sub_requests

    def url(self, org_domain_url: str, api_version: str) -> str:
        return f"{org_domain_url}/services/data/v{api_version}/composite/graph"

    def http_method(self) -> HttpMethod:
        return "POST"

    def request_body(self) -> Json | None:
        json_sub_requests: list[dict[str, Any]] = []

        for reference_id, sub_request in self._sub_requests.items():
            json_sub_request: dict[str, Any] = {
                # Sub-requests use relative URLs, hence the empty-string `org_domain_url`.
                "url": sub_request.url("", self._api_version),
                "method": sub_request.http_method(),
                "referenceId": reference_id.id,
            }

            if sub_request.request_body():
                json_sub_request["body"] = sub_request.request_body()

            json_sub_requests.append(json_sub_request)

        return {
            "graphs": [{"graphId": "graph0", "compositeRequest": json_sub_requests}]
        }

    async def process_response(
        self, status_code: int, json_body: Json | None
    ) -> dict[ReferenceId, str]:
        # This is the case when the composite request itself has errors. Errors of the sub-requests are handled
        # separately.
        if status_code != 200:
            raise SalesforceRestApiError(
                api_errors=_parse_errors(json_body)
            )  # pragma: no cover

        if isinstance(json_body, dict):
            composite_responses = json_body["graphs"][0]["graphResponse"][
                "compositeResponse"
            ]
            result: dict[ReferenceId, str] = {}
            errors: list[InnerSalesforceRestApiError] = []

            for composite_response in composite_responses:
                reference_id = ReferenceId(id=composite_response["referenceId"])
                sub_status_code = composite_response["httpStatusCode"]
                body = composite_response.get("body")

                try:
                    result[reference_id] = await self._sub_requests[
                        reference_id
                    ].process_response(sub_status_code, body)
                except SalesforceRestApiError as rest_api_error:
                    errors.extend(rest_api_error.api_errors)

            if errors:
                raise SalesforceRestApiError(api_errors=errors)

            return result

        raise UnexpectedRestApiResponsePayload(
            "The composite graph API response payload doesn't match the expected structure."
        )  # pragma: no cover


async def _process_records_response(
    status_code: int, json_body: Json | None, download_file_fn: DownloadFileFunction
) -> RecordQueryResult:
    if status_code != 200:
        raise SalesforceRestApiError(api_errors=_parse_errors(json_body))

    if isinstance(json_body, dict):
        return await _parse_record_query_result(json_body, download_file_fn)

    raise UnexpectedRestApiResponsePayload(
        "The API response payload doesn't match the expected structure."
    )  # pragma: no cover


async def _parse_record_query_result(
    json_body: dict[str, Any], download_file_fn: DownloadFileFunction
) -> RecordQueryResult:
    done: bool = json_body["done"]
    total_size: int = json_body["totalSize"]
    next_records_url: str | None = json_body.get("nextRecordsUrl")

    records: list[QueriedRecord] = []
    for record_json in json_body["records"]:
        records.append(await _parse_queried_record(record_json, download_file_fn))

    return RecordQueryResult(
        done=done,
        total_size=total_size,
        records=records,
        next_records_url=next_records_url,
    )


async def _parse_queried_record(
    record_json: dict[str, Any], download_file_fn: DownloadFileFunction
) -> QueriedRecord:
    salesforce_object_type = record_json["attributes"]["type"]

    fields: dict[str, bytes | QueriedRecord | Any] = {}
    sub_query_results = {}
    for key, value in record_json.items():
        if key == "attributes":
            continue

        if isinstance(value, dict):
            value = cast(dict[str, Any], value)
            if "attributes" in value:
                fields[key] = await _parse_queried_record(value, download_file_fn)
            else:
                sub_query_results[key] = await _parse_record_query_result(
                    value, download_file_fn
                )
        elif _is_binary_field(salesforce_object_type, key):
            fields[key] = await download_file_fn(value)
        else:
            fields[key] = value

    return QueriedRecord(
        type=salesforce_object_type, fields=fields, sub_query_results=sub_query_results
    )


def _is_binary_field(salesforce_object_type: str, field_name: str) -> bool:
    return salesforce_object_type == "ContentVersion" and field_name == "VersionData"


def _normalize_record_fields(fields: dict[str, Any]) -> dict[str, Any]:
    return {key: _normalize_field_value(value) for (key, value) in fields.items()}


def _normalize_field_value(value: Any) -> Any:
    if isinstance(value, ReferenceId):
        return f"@{{{value.id}.id}}"

    if isinstance(value, (bytes, bytearray)):
        return standard_b64encode(value).decode("ascii")

    return value


def _parse_errors(json_errors: Json | None) -> list[InnerSalesforceRestApiError]:
    if isinstance(json_errors, list):
        return [
            InnerSalesforceRestApiError(
                message=json_error["message"],
                error_code=json_error["errorCode"],
                fields=json_error.get("fields", []),
            )
            for json_error in json_errors
        ]

    raise UnexpectedRestApiResponsePayload(
        "The API response payload doesn't match the expected structure."
    )  # pragma: no cover
