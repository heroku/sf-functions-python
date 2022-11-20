import binascii
import os
from typing import Any
from unittest.mock import patch

import orjson
from httpx import Response
from starlette.testclient import TestClient

from salesforce_functions._internal.app import app
from salesforce_functions._internal.config import PROJECT_PATH_ENV_VAR


def generate_cloud_event_headers(
    include_optional_attributes: bool = True,
) -> dict[str, str]:
    invocation_id = "56ff961b-61b9-4310-a159-1f997221ccfb"
    headers = {
        "Content-Type": "application/json",
        "ce-id": invocation_id,
        "ce-source": "urn:event:from:salesforce/xx/228.0/00Dxx0000006IYJ/apex/MyFunctionApex:test():7",
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
    }

    if include_optional_attributes:
        headers.update(
            {
                "ce-dataschema": "dataschema TODO",
                "ce-subject": "subject TODO",
                "ce-time": "2022-11-01T12:00:00.000000Z",
            }
        )

    return headers


def generate_sf_context(
    include_optional_attributes: bool = True,
) -> dict[str, str | dict[str, str]]:
    user_context = {
        "orgDomainUrl": "https://d8d000005zejveai-dev-ed.my.salesforce.com",
        "orgId": "00Dxx0000006IYJ",
        "salesforceBaseUrl": "https://d8d000005zejveai-dev-ed.my.salesforce.com",
        "userId": "005xx000001X8Uz",
        "username": "user@example.tld",
    }

    if include_optional_attributes:
        user_context.update(
            {
                "onBehalfOfUserId": "another-user@example.tld",
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
                "apexFQN": "apexFQN TODO",
                "apexId": "apexId TODO",
                "functionInvocationId": "functionInvocationId TODO",
                "functionName": "MyFunction",
                "resource": "http://example.com:8080",
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
        with TestClient(app, raise_server_exceptions=raise_server_exceptions) as client:
            response = client.post("/", headers=headers, json=json, content=content)

    return response
