import binascii
import sys
from datetime import datetime, timezone

import orjson
import pytest
from starlette.datastructures import Headers

from salesforce_functions._internal.cloud_event import (
    CloudEventError,
    SalesforceContext,
    SalesforceFunctionContext,
    SalesforceFunctionsCloudEvent,
    SalesforceUserContext,
)

from .utils import (
    encode_cloud_event_extension,
    generate_cloud_event_headers,
    generate_sf_context,
    generate_sf_function_context,
)


def test_cloud_event() -> None:
    headers = generate_cloud_event_headers()
    body = orjson.dumps({"record_id": 123})
    cloud_event = SalesforceFunctionsCloudEvent.from_http(Headers(headers), body)

    assert cloud_event == SalesforceFunctionsCloudEvent(
        id="00DJS0000000123ABC-d75b3b6ece5011dcabbed4-3c6f7179",
        source="urn:event:from:salesforce/JS/56.0/00DJS0000000123ABC/apex/ExampleClass:example_function():7",
        spec_version="1.0",
        type="com.salesforce.function.invoke.sync",
        data={"record_id": 123},
        data_content_type="application/json",
        data_schema="dataschema TODO",
        subject="subject TODO",
        time=datetime(2023, 1, 19, 10, 9, 12, 476684, tzinfo=timezone.utc),
        sf_context=SalesforceContext(
            api_version="56.0",
            payload_version="0.1",
            user_context=SalesforceUserContext(
                org_id="00DJS0000000123ABC",
                user_id="005JS000000H123",
                on_behalf_of_user_id="005JS000000H456",
                username="user@example.tld",
                salesforce_base_url="https://example-base-url.my.salesforce-sites.com",
                org_domain_url="https://example-domain-url.my.salesforce.com",
            ),
        ),
        sf_function_context=SalesforceFunctionContext(
            access_token="EXAMPLE-TOKEN",
            request_id="00DJS0000000123ABC-d75b3b6ece5011dcabbed4-3c6f7179",
            function_invocation_id="functionInvocationId TODO",
            function_name="ExampleProject.examplefunction",
            apex_id="apexId TODO",
            apex_fqn="ExampleClass:example_function():7",
            resource="https://examplefunction-cod-mni.crag-123abc.evergreen.space",
        ),
    )


def test_minimal_cloud_event() -> None:
    headers = generate_cloud_event_headers(include_optional_attributes=False)
    body = b""
    cloud_event = SalesforceFunctionsCloudEvent.from_http(Headers(headers), body)

    assert cloud_event == SalesforceFunctionsCloudEvent(
        id="00DJS0000000123ABC-d75b3b6ece5011dcabbed4-3c6f7179",
        source="urn:event:from:salesforce/JS/56.0/00DJS0000000123ABC/apex/ExampleClass:example_function():7",
        spec_version="1.0",
        type="com.salesforce.function.invoke.sync",
        data=None,
        data_content_type="application/json",
        data_schema=None,
        subject=None,
        time=None,
        sf_context=SalesforceContext(
            api_version="56.0",
            payload_version="0.1",
            user_context=SalesforceUserContext(
                org_id="00DJS0000000123ABC",
                user_id="005JS000000H123",
                on_behalf_of_user_id=None,
                username="user@example.tld",
                salesforce_base_url="https://example-base-url.my.salesforce-sites.com",
                org_domain_url="https://example-domain-url.my.salesforce.com",
            ),
        ),
        sf_function_context=SalesforceFunctionContext(
            access_token="EXAMPLE-TOKEN",
            request_id="00DJS0000000123ABC-d75b3b6ece5011dcabbed4-3c6f7179",
            function_invocation_id=None,
            function_name=None,
            apex_id=None,
            apex_fqn=None,
            resource=None,
        ),
    )


def test_invalid_content_type_missing() -> None:
    headers: dict[str, str] = {}
    expected_message = r"Content-Type must be 'application/json' not ''$"

    with pytest.raises(CloudEventError, match=expected_message):
        SalesforceFunctionsCloudEvent.from_http(Headers(headers), b"")


def test_invalid_content_type_unsupported() -> None:
    headers = {"Content-Type": "text/plain"}
    expected_message = r"Content-Type must be 'application/json' not 'text/plain'$"

    with pytest.raises(CloudEventError, match=expected_message):
        SalesforceFunctionsCloudEvent.from_http(Headers(headers), b"")


def test_invalid_body_not_json() -> None:
    headers = generate_cloud_event_headers()
    body = b"Not json"
    expected_message = r"Data payload is not valid JSON: unexpected character: .+"

    with pytest.raises(CloudEventError, match=expected_message):
        SalesforceFunctionsCloudEvent.from_http(Headers(headers), body)


def test_invalid_event_time() -> None:
    headers = generate_cloud_event_headers()
    headers["ce-time"] = "12:00"

    if sys.version_info < (3, 11):
        expected_message = r"Unable to parse event time: invalid literal .+"
    else:
        expected_message = r"Unable to parse event time: Invalid isoformat string: .+"

    with pytest.raises(CloudEventError, match=expected_message):
        SalesforceFunctionsCloudEvent.from_http(Headers(headers), b"")


@pytest.mark.parametrize(
    "header_name",
    [
        "ce-id",
        "ce-sfcontext",
        "ce-sffncontext",
        "ce-source",
        "ce-specversion",
        "ce-type",
    ],
)
def test_invalid_cloud_event_header_missing(header_name: str) -> None:
    headers = generate_cloud_event_headers()
    headers.pop(header_name)
    expected_message = rf"Missing required header '{header_name}'$"

    with pytest.raises(CloudEventError, match=expected_message):
        SalesforceFunctionsCloudEvent.from_http(Headers(headers), b"")


@pytest.mark.parametrize("extension_name", ["sfcontext", "sffncontext"])
def test_invalid_cloud_event_extension_not_base64(extension_name: str) -> None:
    headers = generate_cloud_event_headers()
    headers[f"ce-{extension_name}"] = "Not base64"
    expected_message = (
        rf"{extension_name} is not correctly encoded: Invalid base64-encoded string: .+"
    )

    with pytest.raises(CloudEventError, match=expected_message):
        SalesforceFunctionsCloudEvent.from_http(Headers(headers), b"")


@pytest.mark.parametrize("extension_name", ["sfcontext", "sffncontext"])
def test_invalid_cloud_event_extension_not_json(extension_name: str) -> None:
    headers = generate_cloud_event_headers()
    headers[f"ce-{extension_name}"] = binascii.b2a_base64(b"Not json").decode("ascii")
    expected_message = rf"{extension_name} is not valid JSON: unexpected character: .+"

    with pytest.raises(CloudEventError, match=expected_message):
        SalesforceFunctionsCloudEvent.from_http(Headers(headers), b"")


@pytest.mark.parametrize("extension_name", ["sfcontext", "sffncontext"])
def test_invalid_cloud_event_extension_not_dict(extension_name: str) -> None:
    headers = generate_cloud_event_headers()
    headers[f"ce-{extension_name}"] = encode_cloud_event_extension("Not a dict")
    expected_message = rf"{extension_name} contains unexpected data type: .+"

    with pytest.raises(CloudEventError, match=expected_message):
        SalesforceFunctionsCloudEvent.from_http(Headers(headers), b"")


def test_invalid_sfcontext_extension_field_missing() -> None:
    headers = generate_cloud_event_headers()
    sf_context = generate_sf_context()
    sf_context.pop("userContext")
    headers["ce-sfcontext"] = encode_cloud_event_extension(sf_context)
    expected_message = r"sfcontext missing required key 'userContext'$"

    with pytest.raises(CloudEventError, match=expected_message):
        SalesforceFunctionsCloudEvent.from_http(Headers(headers), b"")


def test_invalid_sffncontext_extension_field_missing() -> None:
    headers = generate_cloud_event_headers()
    sf_function_context = generate_sf_function_context(invocation_id=headers["ce-id"])
    sf_function_context.pop("accessToken")
    headers["ce-sffncontext"] = encode_cloud_event_extension(sf_function_context)
    expected_message = r"sffncontext missing required key 'accessToken'$"

    with pytest.raises(CloudEventError, match=expected_message):
        SalesforceFunctionsCloudEvent.from_http(Headers(headers), b"")
