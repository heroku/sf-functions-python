import binascii
import os
from typing import Any
from unittest.mock import patch

import orjson
from httpx import Response
from starlette.testclient import TestClient

from salesforce_functions._internal.app import PROJECT_PATH_ENV_VAR, asgi_app

WIREMOCK_SERVER_URL = "http://localhost:12345"


def generate_cloud_event_headers(
    include_optional_attributes: bool = True,
) -> dict[str, str]:
    invocation_id = "00DJS0000000123ABC-d75b3b6ece5011dcabbed4-3c6f7179"
    headers = {
        "Content-Type": "application/json",
        "ce-id": invocation_id,
        "ce-source": "urn:event:from:salesforce/JS/56.0/00DJS0000000123ABC/apex/ExampleClass:example_function():7",
        "ce-specversion": "1.0",
        "ce-type": "com.salesforce.function.invoke.sync",
        "ce-sfcontext": encode_cloud_event_extension(
            generate_sf_context(include_optional_attributes=include_optional_attributes)
        ),
        "ce-sffncontext": encode_cloud_event_extension(
            generate_sf_function_context(
                invocation_id, include_optional_attributes=include_optional_attributes
            )
        ),
        "x-request-id": invocation_id,
    }

    if include_optional_attributes:
        headers.update(
            {
                "ce-dataschema": "dataschema TODO",
                "ce-subject": "subject TODO",
                "ce-time": "2023-01-19T10:09:12.476684Z",
            }
        )

    return headers


def generate_sf_context(
    include_optional_attributes: bool = True,
) -> dict[str, str | dict[str, str]]:
    user_context = {
        "orgId": "00DJS0000000123ABC",
        "orgDomainUrl": "https://example-domain-url.my.salesforce.com",
        "salesforceBaseUrl": "https://example-base-url.my.salesforce-sites.com",
        "salesforceInstance": "swe1",
        "userId": "005JS000000H123",
        "username": "user@example.tld",
    }

    if include_optional_attributes:
        user_context.update(
            {
                "onBehalfOfUserId": "005JS000000H456",
            }
        )

    return {
        "apiVersion": "56.0",
        "payloadVersion": "0.1",
        "userContext": user_context,
    }


def generate_sf_function_context(
    invocation_id: str, include_optional_attributes: bool = True
) -> dict[str, str]:
    sf_function_context = {
        "accessToken": "EXAMPLE-TOKEN",
        "requestId": invocation_id,
    }

    if include_optional_attributes:
        sf_function_context.update(
            {
                "apexFQN": "ExampleClass:example_function():7",
                "apexId": "apexId TODO",
                "deadline": "2023-01-19T10:11:12.468085Z",
                "functionInvocationId": "functionInvocationId TODO",
                "functionName": "ExampleProject.examplefunction",
                "invokingNamespace": "",
                "resource": "https://examplefunction-cod-mni.crag-123abc.evergreen.space",
            }
        )

    return sf_function_context


def encode_cloud_event_extension(data: Any) -> str:
    json = orjson.dumps(data)
    return binascii.b2a_base64(json).decode("ascii")


def invoke_function(
    fixture_path: str,
    headers: dict[str, str] | None = None,
    json: Any = None,
    content: Any = None,
    raise_server_exceptions: bool = True,
) -> Response:
    if headers is None:
        headers = generate_cloud_event_headers()

    with patch.dict(os.environ, {PROJECT_PATH_ENV_VAR: fixture_path}):
        with TestClient(
            asgi_app, raise_server_exceptions=raise_server_exceptions
        ) as client:
            response = client.post("/", headers=headers, json=json, content=content)

    return response
