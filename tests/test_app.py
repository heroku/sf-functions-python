import os
import sys
from unittest.mock import patch

import pytest
from pytest import CaptureFixture
from starlette.testclient import TestClient

from salesforce_functions._internal.app import app
from salesforce_functions._internal.config import PROJECT_PATH_ENV_VAR

from .utils import (
    WIREMOCK_SERVER_URL,
    encode_cloud_event_extension,
    generate_cloud_event_headers,
    generate_sf_context,
    invoke_function,
)


def test_health_check(capsys: CaptureFixture[str]) -> None:
    response = invoke_function(
        "tests/fixtures/basic", headers={"x-health-check": "true"}
    )
    assert response.status_code == 200
    assert response.headers.get("Content-Type") == "application/json"
    assert response.json() == "OK"

    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == ""


def test_empty_payload_and_response(capsys: CaptureFixture[str]) -> None:
    response = invoke_function("tests/fixtures/basic")
    assert response.status_code == 200
    assert response.headers.get("Content-Type") == "application/json"
    assert response.json() is None

    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == ""


def test_event_attributes() -> None:
    payload = {"record_id": 12345}
    response = invoke_function("tests/fixtures/returns_event", json=payload)
    assert response.status_code == 200
    assert response.headers.get("Content-Type") == "application/json"
    assert response.json() == {
        "data": payload,
        "id": "56ff961b-61b9-4310-a159-1f997221ccfb",
        "source": "urn:event:from:salesforce/xx/228.0/00Dxx0000006IYJ/apex/MyFunctionApex:test():7",
        "time": "2022-11-01T12:30:10.123456+00:00",
        "type": "com.salesforce.function.invoke.sync",
    }


def test_minimal_event_attributes() -> None:
    response = invoke_function(
        "tests/fixtures/returns_event",
        headers=generate_cloud_event_headers(include_optional_attributes=False),
    )
    assert response.status_code == 200
    assert response.headers.get("Content-Type") == "application/json"
    assert response.json() == {
        "data": None,
        "id": "56ff961b-61b9-4310-a159-1f997221ccfb",
        "source": "urn:event:from:salesforce/xx/228.0/00Dxx0000006IYJ/apex/MyFunctionApex:test():7",
        "time": None,
        "type": "com.salesforce.function.invoke.sync",
    }


def test_context_attributes() -> None:
    payload = {"record_id": 12345}
    response = invoke_function("tests/fixtures/returns_context", json=payload)
    assert response.status_code == 200
    assert response.headers.get("Content-Type") == "application/json"
    assert response.json() == {
        "org": {
            "base_url": "https://example-base-url.my.salesforce-sites.com",
            "data_api": "REMOVED",
            "domain_url": "https://example-domain-url.my.salesforce.com",
            "id": "00Dxx0000006IYJ",
            "user": {
                "id": "005xx000001X8Uz",
                "on_behalf_of_user_id": "another-user@example.tld",
                "username": "user@example.tld",
            },
        },
    }


def test_minimal_context_attributes() -> None:
    response = invoke_function(
        "tests/fixtures/returns_context",
        headers=generate_cloud_event_headers(include_optional_attributes=False),
    )
    assert response.status_code == 200
    assert response.headers.get("Content-Type") == "application/json"
    assert response.json() == {
        "org": {
            "base_url": "https://example-base-url.my.salesforce-sites.com",
            "data_api": "REMOVED",
            "domain_url": "https://example-domain-url.my.salesforce.com",
            "id": "00Dxx0000006IYJ",
            "user": {
                "id": "005xx000001X8Uz",
                "on_behalf_of_user_id": None,
                "username": "user@example.tld",
            },
        },
    }


@pytest.mark.requires_wiremock
def test_data_api() -> None:
    sf_context = generate_sf_context()
    assert isinstance(sf_context["userContext"], dict)
    sf_context["userContext"]["orgDomainUrl"] = WIREMOCK_SERVER_URL

    headers = generate_cloud_event_headers()
    headers["ce-sfcontext"] = encode_cloud_event_extension(sf_context)
    response = invoke_function("tests/fixtures/data_api", headers=headers)

    assert response.status_code == 200
    assert response.headers.get("Content-Type") == "application/json"
    assert response.json() == "a00B000000FSkcvIAD"


def test_logging(capsys: CaptureFixture[str]) -> None:
    response = invoke_function("tests/fixtures/logging")
    assert response.status_code == 200

    output = capsys.readouterr()
    # Only `info` log levels and above should be output by default.
    assert "level=debug" not in output.out
    assert (
        output.out
        == """Print works but output isn't structured
invocationId=56ff961b-61b9-4310-a159-1f997221ccfb level=info msg="Info message"
invocationId=56ff961b-61b9-4310-a159-1f997221ccfb level=warning msg="Warning message"
invocationId=56ff961b-61b9-4310-a159-1f997221ccfb level=error msg="Error message"
invocationId=56ff961b-61b9-4310-a159-1f997221ccfb level=critical msg="Critical message"
record_id=12345 invocationId=56ff961b-61b9-4310-a159-1f997221ccfb level=info msg="Info message with custom metadata"
"""
    )
    assert output.err == ""


def test_template_function() -> None:
    # TODO: Create a WireMock mapping for the template function's data API usage, and make
    # this test actually invoke the function, rather than just performing a health check.
    # Or alternatively, stop using the data API in the template function so the template
    # works out of the box in production without requiring permissions setup.
    response = invoke_function(
        "tests/fixtures/template", headers={"x-health-check": "true"}
    )
    assert response.status_code == 200
    assert response.headers.get("Content-Type") == "application/json"
    assert response.json() == "OK"


def test_invalid_function() -> None:
    expected_message = r"Function failed to load! File not found: .+$"

    try:
        with pytest.raises(RuntimeError, match=expected_message):
            invoke_function("tests/fixtures/invalid_function_missing_module")

        # The error handling in `app.lifespan()` sets a custom `sys.tracebacklimit` to
        # truncate the traceback, to improve readability of the error message.
        assert getattr(sys, "tracebacklimit", None) == 0
    finally:
        try:
            # Prevent the traceback output in later tests from being truncated too.
            del sys.tracebacklimit
        except AttributeError:
            pass


def test_cloud_event_headers_missing(capsys: CaptureFixture[str]) -> None:
    response = invoke_function("tests/fixtures/basic", headers={})

    expected_message = (
        "Could not parse CloudEvent: Content-Type must be 'application/json' not ''"
    )
    assert response.status_code == 400
    assert response.headers.get("Content-Type") == "application/json"
    assert response.json() == expected_message

    output = capsys.readouterr()
    assert output.out == f'level=error msg="{expected_message}"\n'
    assert output.err == ""


def test_cloud_event_body_not_json(capsys: CaptureFixture[str]) -> None:
    response = invoke_function("tests/fixtures/basic", content="Not json")

    expected_message = (
        "Could not parse CloudEvent: Data payload is not valid JSON:"
        " unexpected character: line 1 column 1 (char 0)"
    )
    assert response.status_code == 400
    assert response.headers.get("Content-Type") == "application/json"
    assert response.json() == expected_message

    output = capsys.readouterr()
    assert output.out == f'level=error msg="{expected_message}"\n'
    assert output.err == ""


def test_function_raises_exception_at_runtime(capsys: CaptureFixture[str]) -> None:
    assert not hasattr(sys, "tracebacklimit"), (
        "A custom `sys.tracebacklimit` is still defined but should not be, otherwise it"
        " will affect this test. Check earlier tests aren't missing a cleanup step."
    )

    response = invoke_function("tests/fixtures/raises_exception_at_runtime")

    expected_message = "Exception occurred whilst executing function: ZeroDivisionError: division by zero"
    assert response.status_code == 500
    assert response.headers.get("Content-Type") == "application/json"
    assert response.json() == expected_message

    output = capsys.readouterr()
    assert output.out.endswith(
        rf"""
ZeroDivisionError: division by zero
invocationId=56ff961b-61b9-4310-a159-1f997221ccfb level=error msg="{expected_message}"
"""
    )
    assert output.err == ""


def test_return_value_not_serializable(capsys: CaptureFixture[str]) -> None:
    response = invoke_function("tests/fixtures/return_value_not_serializable")

    expected_message = "Function return value cannot be serialized: TypeError: Type is not JSON serializable: set"
    assert response.status_code == 500
    assert response.headers.get("Content-Type") == "application/json"
    assert response.json() == expected_message

    output = capsys.readouterr()
    assert (
        output.out
        == f'invocationId=56ff961b-61b9-4310-a159-1f997221ccfb level=error msg="{expected_message}"\n'
    )
    assert output.err == ""


def test_internal_error(capsys: CaptureFixture[str]) -> None:
    with patch(
        "salesforce_functions._internal.app.SalesforceFunctionsCloudEvent.from_http",
        side_effect=ValueError("Some internal error"),
    ):
        response = invoke_function(
            "tests/fixtures/basic", raise_server_exceptions=False
        )

    expected_message = "Internal error: ValueError: Some internal error"
    assert response.status_code == 500
    assert response.headers.get("Content-Type") == "application/json"
    assert response.json() == expected_message

    output = capsys.readouterr()
    assert output.out == f'level=error msg="{expected_message}"\n'
    assert output.err == ""


def test_nonexistent_path() -> None:
    with patch.dict(os.environ, {PROJECT_PATH_ENV_VAR: "tests/fixtures/basic"}):
        with TestClient(app) as client:
            response = client.post("/nonexistent")

    assert response.status_code == 404


def test_unsupported_http_method_get() -> None:
    with patch.dict(os.environ, {PROJECT_PATH_ENV_VAR: "tests/fixtures/basic"}):
        with TestClient(app) as client:
            response = client.get("/")

    assert response.status_code == 405


def test_unsupported_http_method_delete() -> None:
    with patch.dict(os.environ, {PROJECT_PATH_ENV_VAR: "tests/fixtures/basic"}):
        with TestClient(app) as client:
            response = client.delete("/")

    assert response.status_code == 405
