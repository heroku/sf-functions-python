import binascii
from dataclasses import dataclass
from typing import Any, Optional

import orjson
from starlette.datastructures import Headers


@dataclass(frozen=True, slots=True)
class SalesforceUserContext:
    org_id: str
    user_id: str
    on_behalf_of_user_id: Optional[str]
    username: str
    salesforce_base_url: str
    org_domain_url: str


@dataclass(frozen=True, slots=True)
class SalesforceContext:
    api_version: str
    payload_version: str
    user_context: SalesforceUserContext

    @classmethod
    def from_base64_json(cls, base64_json: str):
        try:
            data = parseBase64Json(base64_json)
        except (binascii.Error, UnicodeDecodeError) as e:
            raise CloudEventError(f"sfcontext is not correctly encoded: {e}")
        except orjson.JSONDecodeError as e:
            raise CloudEventError(f"sfcontext is not valid JSON: {e}")

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
            raise CloudEventError(f"sfcontext contains unexpected data type: {e}")
        except KeyError as e:
            raise CloudEventError(f"sfcontext missing required key {e}")


@dataclass(frozen=True, slots=True)
class SalesforceFunctionContext:
    access_token: str
    request_id: str
    function_invocation_id: Optional[str]
    function_name: Optional[str]
    # TODO: Should these be "apex*" or "apexClass*"?
    apex_id: Optional[str]
    apex_fqn: Optional[str]
    resource: Optional[str]

    @classmethod
    def from_base64_json(cls, base64_json: str):
        try:
            data = parseBase64Json(base64_json)
        except (binascii.Error, UnicodeDecodeError) as e:
            raise CloudEventError(f"sffncontext is not correctly encoded: {e}")
        except orjson.JSONDecodeError as e:
            raise CloudEventError(f"sffncontext is not valid JSON: {e}")

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
            raise CloudEventError(f"sffncontext contains unexpected data type: {e}")
        except KeyError as e:
            raise CloudEventError(f"sffncontext missing required key {e}")


@dataclass(frozen=True, slots=True)
class SalesforceFunctionsCloudEvent:
    id: str
    source: str
    spec_version: str
    type: str
    data: Optional[Any]
    data_content_type: str
    data_schema: Optional[str]
    subject: Optional[str]
    time: Optional[str]
    sf_context: SalesforceContext
    sf_function_context: SalesforceFunctionContext

    @classmethod
    def from_http(cls, headers: Headers, body: bytes):
        content_type = headers.get("Content-Type", "")

        if not content_type.startswith("application/json"):
            raise CloudEventError("Content-Type must be 'application/json'")

        try:
            data = orjson.loads(body) if body else None
        except orjson.JSONDecodeError as e:
            raise CloudEventError(f"Data payload is not valid JSON: {e}")

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
                time=headers.get("ce-time"),
                sf_context=SalesforceContext.from_base64_json(headers["ce-sfcontext"]),
                sf_function_context=SalesforceFunctionContext.from_base64_json(
                    headers["ce-sffncontext"]
                ),
            )
        except KeyError as e:
            raise CloudEventError(f"Missing required header {e}")


def parseBase64Json(base64_json: str) -> Any:
    return orjson.loads(binascii.a2b_base64(base64_json))


class CloudEventError(Exception):
    pass
