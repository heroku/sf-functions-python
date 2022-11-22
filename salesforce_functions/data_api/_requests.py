from typing import Any, Generic, Literal, TypeVar, cast
from urllib.parse import urlencode

from .exceptions import (
    InnerSalesforceRestApiError,
    MissingIdFieldError,
    SalesforceRestApiError,
    UnexpectedRestApiResponsePayload,
)
from .record import QueriedRecord, Record, RecordQueryResult
from .reference_id import ReferenceId

HttpMethod = Literal["GET", "POST", "PATCH", "DELETE"]
Json = dict[str, Any] | list[Any]

T = TypeVar("T")


class RestApiRequest(Generic[T]):
    def url(self, org_domain_url: str, api_version: str) -> str:
        raise NotImplementedError

    def http_method(self) -> HttpMethod:
        raise NotImplementedError

    def request_body(self) -> Json | None:
        raise NotImplementedError

    def process_response(self, status_code: int, json_body: Json) -> T:
        raise NotImplementedError


class QueryRecordsRestApiRequest(RestApiRequest[RecordQueryResult]):
    def __init__(self, soql: str):
        self._soql = soql

    def url(self, org_domain_url: str, api_version: str) -> str:
        return f"{org_domain_url}/services/data/v{api_version}/query?{urlencode({'q': self._soql})}"

    def http_method(self) -> HttpMethod:
        return "GET"

    def request_body(self) -> Json | None:
        return None

    def process_response(self, status_code: int, json_body: Json) -> RecordQueryResult:
        return _process_records_response(status_code, json_body)


class QueryNextRecordsRestApiRequest(RestApiRequest[RecordQueryResult]):
    def __init__(self, next_records_path: str):
        self._next_records_path = next_records_path

    def url(self, org_domain_url: str, api_version: str) -> str:
        return f"{org_domain_url}{self._next_records_path}"

    def http_method(self) -> HttpMethod:
        return "GET"

    def request_body(self) -> Json | None:
        return None

    def process_response(self, status_code: int, json_body: Json) -> RecordQueryResult:
        return _process_records_response(status_code, json_body)


class CreateRecordRestApiRequest(RestApiRequest[str]):
    def __init__(self, record: Record):
        self._record = record

    def url(self, org_domain_url: str, api_version: str) -> str:
        return f"{org_domain_url}/services/data/v{api_version}/sobjects/{self._record.type}"

    def http_method(self) -> HttpMethod:
        return "POST"

    def request_body(self) -> Json | None:
        return _normalize_record_fields(self._record.fields)

    def process_response(self, status_code: int, json_body: Json) -> str:
        if status_code != 201:
            raise SalesforceRestApiError(_parse_errors(json_body))

        if isinstance(json_body, dict):
            return str(json_body["id"])

        raise UnexpectedRestApiResponsePayload()


class UpdateRecordRestApiRequest(RestApiRequest[str]):
    def __init__(self, record: Record):
        if "Id" not in record.fields:
            raise MissingIdFieldError()

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

    def process_response(self, status_code: int, json_body: Json) -> str:
        if status_code != 204:
            raise SalesforceRestApiError(_parse_errors(json_body))

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

    def process_response(self, status_code: int, json_body: Json) -> str:
        if status_code != 204:
            raise SalesforceRestApiError(_parse_errors(json_body))

        return self._record_id


class CompositeGraphRestApiRequest(RestApiRequest[dict[ReferenceId, str]]):
    def __init__(
        self,
        base_uri: str,
        api_version: str,
        sub_requests: dict[ReferenceId, RestApiRequest[str]],
    ):
        self._base_uri = base_uri
        self._api_version = api_version
        self._sub_requests = sub_requests

    def url(self, org_domain_url: str, api_version: str) -> str:
        return f"{self._base_uri}/services/data/v{api_version}/composite/graph"

    def http_method(self) -> HttpMethod:
        return "POST"

    def request_body(self) -> Json | None:
        json_sub_requests: list[dict[str, Any]] = []

        for reference_id, sub_request in self._sub_requests.items():
            json_sub_request: dict[str, Any] = {
                "url": sub_request.url(self._base_uri, self._api_version).removeprefix(
                    self._base_uri
                ),
                "method": sub_request.http_method(),
                "referenceId": reference_id.id,
            }

            if sub_request.request_body():
                json_sub_request["body"] = sub_request.request_body()

            json_sub_requests.append(json_sub_request)

        return {
            "graphs": [{"graphId": "graph0", "compositeRequest": json_sub_requests}]
        }

    def process_response(
        self, status_code: int, json_body: Json
    ) -> dict[ReferenceId, str]:
        # This is the case when the composite request itself has errors. Errors of the sub-requests are handled
        # separately.
        if status_code != 200:
            raise SalesforceRestApiError(_parse_errors(json_body))

        if isinstance(json_body, dict):
            composite_responses = json_body["graphs"][0]["graphResponse"][
                "compositeResponse"
            ]
            result: dict[ReferenceId, str] = {}
            errors: list[InnerSalesforceRestApiError] = []

            for composite_response in composite_responses:
                reference_id = ReferenceId(composite_response["referenceId"])
                sub_status_code = composite_response["httpStatusCode"]
                body = composite_response.get("body")

                try:
                    result[reference_id] = self._sub_requests[
                        reference_id
                    ].process_response(sub_status_code, body)
                except SalesforceRestApiError as rest_api_error:
                    errors.extend(rest_api_error.api_errors)

            if errors:
                raise SalesforceRestApiError(errors)

            return result

        raise UnexpectedRestApiResponsePayload()


def _process_records_response(status_code: int, json_body: Json) -> RecordQueryResult:
    if status_code != 200:
        raise SalesforceRestApiError(_parse_errors(json_body))

    if isinstance(json_body, dict):
        done: bool = json_body["done"]
        total_size: int = json_body["totalSize"]
        next_records_url: str | None = json_body.get("nextRecordsUrl")

        records: list[QueriedRecord] = []
        for record_json in json_body["records"]:
            salesforce_object_type = record_json["attributes"]["type"]

            fields = {}
            sub_query_results = {}
            for key, value in record_json.items():
                if key == "attributes":
                    continue

                if isinstance(value, dict):
                    sub_query_results[key] = _process_records_response(
                        status_code, cast(dict[str, Any], value)
                    )
                else:
                    fields[key] = value

            records.append(
                QueriedRecord(salesforce_object_type, fields, sub_query_results)
            )

        return RecordQueryResult(done, total_size, records, next_records_url)

    raise UnexpectedRestApiResponsePayload()


def _normalize_record_fields(fields: dict[str, Any]) -> dict[str, Any]:
    return {key: _normalize_field_value(value) for (key, value) in fields.items()}


def _normalize_field_value(value: Any) -> Any:
    return f"@{{{value.id}.id}}" if isinstance(value, ReferenceId) else value


def _parse_errors(json_errors: Json) -> list[InnerSalesforceRestApiError]:
    if isinstance(json_errors, list):
        return [
            InnerSalesforceRestApiError(
                json_error["message"],
                json_error["errorCode"],
                json_error.get("fields", []),
            )
            for json_error in json_errors
        ]

    raise UnexpectedRestApiResponsePayload()
