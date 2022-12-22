import binascii
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import orjson
from starlette.datastructures import Headers

if sys.version_info < (3, 11):
    import dateutil.parser  # pragma: no-cover-python-gte-311
else:
    pass  # pragma: no-cover-python-lt-311


@dataclass(frozen=True, slots=True)
class SalesforceUserContext:
    org_id: str
    user_id: str
    on_behalf_of_user_id: str | None
    username: str
    salesforce_base_url: str
    # TODO: Figure out discrepancy with schema: https://github.com/forcedotcom/sf-fx-schema/issues/7
    org_domain_url: str


@dataclass(frozen=True, slots=True)
class SalesforceContext:
    api_version: str
    payload_version: str
    user_context: SalesforceUserContext

    @classmethod
    def from_base64_json(cls, base64_json: str) -> "SalesforceContext":
        try:
            data = parse_base64_json(base64_json)
        except (binascii.Error, UnicodeDecodeError) as e:
            raise CloudEventError(f"sfcontext is not correctly encoded: {e}") from e
        except orjson.JSONDecodeError as e:
            raise CloudEventError(f"sfcontext is not valid JSON: {e}") from e

        try:
            user_context = data["userContext"]
            return cls(
                api_version=data["apiVersion"],
                payload_version=data["payloadVersion"],
                user_context=SalesforceUserContext(
                    org_id=user_context["orgId"],
                    user_id=user_context["userId"],
                    on_behalf_of_user_id=user_context.get("onBehalfOfUserId"),
                    username=user_context["username"],
                    salesforce_base_url=user_context["salesforceBaseUrl"],
                    org_domain_url=user_context["orgDomainUrl"],
                ),
            )
        except TypeError as e:
            raise CloudEventError(
                f"sfcontext contains unexpected data type: {e}"
            ) from e
        except KeyError as e:
            raise CloudEventError(f"sfcontext missing required key {e}") from e


@dataclass(frozen=True, slots=True)
class SalesforceFunctionContext:
    # TODO: Figure out discrepancy with schema: https://github.com/forcedotcom/sf-fx-schema/issues/8
    access_token: str
    request_id: str
    function_invocation_id: str | None
    function_name: str | None
    apex_id: str | None
    apex_fqn: str | None
    resource: str | None

    @classmethod
    def from_base64_json(cls, base64_json: str) -> "SalesforceFunctionContext":
        try:
            data = parse_base64_json(base64_json)
        except (binascii.Error, UnicodeDecodeError) as e:
            raise CloudEventError(f"sffncontext is not correctly encoded: {e}") from e
        except orjson.JSONDecodeError as e:
            raise CloudEventError(f"sffncontext is not valid JSON: {e}") from e

        try:
            return cls(
                access_token=data["accessToken"],
                request_id=data["requestId"],
                function_invocation_id=data.get("functionInvocationId"),
                function_name=data.get("functionName"),
                apex_id=data.get("apexId"),
                apex_fqn=data.get("apexFQN"),
                resource=data.get("resource"),
            )
        except TypeError as e:
            raise CloudEventError(
                f"sffncontext contains unexpected data type: {e}"
            ) from e
        except KeyError as e:
            raise CloudEventError(f"sffncontext missing required key {e}") from e


@dataclass(frozen=True, slots=True)
class SalesforceFunctionsCloudEvent:
    id: str
    source: str
    spec_version: str
    type: str
    data: Any | None
    data_content_type: str
    data_schema: str | None
    subject: str | None
    time: datetime | None
    sf_context: SalesforceContext
    sf_function_context: SalesforceFunctionContext

    @classmethod
    def from_http(
        cls, headers: Headers, body: bytes
    ) -> "SalesforceFunctionsCloudEvent":
        content_type = headers.get("Content-Type", "")

        if not content_type.startswith("application/json"):
            raise CloudEventError(
                f"Content-Type must be 'application/json' not '{content_type}'"
            )

        try:
            data = orjson.loads(body) if body else None
        except orjson.JSONDecodeError as e:
            raise CloudEventError(f"Data payload is not valid JSON: {e}") from e

        try:
            return cls(
                id=headers["ce-id"],
                source=headers["ce-source"],
                spec_version=headers["ce-specversion"],
                type=headers["ce-type"],
                data=data,
                data_content_type=content_type,
                data_schema=headers.get("ce-dataschema"),
                subject=headers.get("ce-subject"),
                time=_parse_event_time(headers.get("ce-time")),
                sf_context=SalesforceContext.from_base64_json(headers["ce-sfcontext"]),
                sf_function_context=SalesforceFunctionContext.from_base64_json(
                    headers["ce-sffncontext"]
                ),
            )
        except KeyError as e:
            raise CloudEventError(f"Missing required header {e}") from e


def parse_base64_json(base64_json: str) -> Any:
    return orjson.loads(binascii.a2b_base64(base64_json))


def _parse_event_time(time_string: str | None) -> datetime | None:
    if time_string is None:
        return None

    try:
        # Prior to Python 3.11, the stdlib's `datetime.fromisoformat()` didn't fully support
        # RFC 3339 format dates, so an external library has to be used instead. This library
        # is not used on newer Pythons to keep dependencies to a minimum.
        if sys.version_info < (3, 11):
            return dateutil.parser.isoparse(
                time_string
            )  # pragma: no-cover-python-gte-311

        return datetime.fromisoformat(time_string)  # pragma: no-cover-python-lt-311
    except (TypeError, ValueError) as e:
        raise CloudEventError(f"Unable to parse event time: {e}") from e


class CloudEventError(Exception):
    pass
