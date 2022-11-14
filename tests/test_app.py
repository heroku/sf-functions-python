import os
import sys
from unittest.mock import patch

import pytest
from pytest import CaptureFixture
from starlette.testclient import TestClient

from .utils import generate_cloud_event_headers, invoke_function
from salesforce_functions._internal.app import app


def test_health_check(capsys: CaptureFixture[str]):
    response = invoke_function(
        "tests/fixtures/basic", headers={"x-health-check": "true"}
    )
    assert response.status_code == 200
    assert response.headers.get("Content-Type") == "application/json"
    assert response.json() == "OK"

    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == ""


def test_empty_payload_and_response(capsys: CaptureFixture[str]):
    response = invoke_function("tests/fixtures/basic")
    assert response.status_code == 200
    assert response.headers.get("Content-Type") == "application/json"
    assert response.json() is None

    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == ""


def test_event_attributes():
    payload = {"record_id": 12345}
    response = invoke_function("tests/fixtures/returns_event", json=payload)
    assert response.status_code == 200
    assert response.headers.get("Content-Type") == "application/json"
    assert response.json() == {
        "data": payload,
        "data_content_type": "application/json",
        "data_schema": "dataschema TODO",
        "id": "56ff961b-61b9-4310-a159-1f997221ccfb",
        "source": "urn:event:from:salesforce/xx/228.0/00Dxx0000006IYJ/apex/MyFunctionApex:test():7",
        "time": "2022-11-01T12:00:00.000000Z",
        "type": "com.salesforce.function.invoke.sync",
    }


def test_minimal_event_attributes():
    response = invoke_function(
        "tests/fixtures/returns_event",
        headers=generate_cloud_event_headers(include_optional_attributes=False),
    )
    assert response.status_code == 200
    assert response.headers.get("Content-Type") == "application/json"
    assert response.json() == {
        "data": None,
        "data_content_type": "application/json",
        "data_schema": None,
        "id": "56ff961b-61b9-4310-a159-1f997221ccfb",
        "source": "urn:event:from:salesforce/xx/228.0/00Dxx0000006IYJ/apex/MyFunctionApex:test():7",
        "time": None,
        "type": "com.salesforce.function.invoke.sync",
    }


def test_context_attributes():
    payload = {"record_id": 12345}
    response = invoke_function("tests/fixtures/returns_context", json=payload)
    assert response.status_code == 200
    assert response.headers.get("Content-Type") == "application/json"
    assert response.json() == {
        "org": {
            "api_version": "56.0",
            "base_url": "https://d8d000005zejveai-dev-ed.my.salesforce.com",
            "data_api": None,
            "domain_url": "https://d8d000005zejveai-dev-ed.my.salesforce.com",
            "id": "00Dxx0000006IYJ",
            "user": {
                "id": "005xx000001X8Uz",
                "on_behalf_of_user_id": "another-user@example.tld",
                "username": "user@example.tld",
            },
        },
    }


def test_minimal_context_attributes():
    response = invoke_function(
        "tests/fixtures/returns_context",
        headers=generate_cloud_event_headers(include_optional_attributes=False),
    )
    assert response.status_code == 200
    assert response.headers.get("Content-Type") == "application/json"
    assert response.json() == {
        "org": {
            "api_version": "56.0",
            "base_url": "https://d8d000005zejveai-dev-ed.my.salesforce.com",
            "data_api": None,
            "domain_url": "https://d8d000005zejveai-dev-ed.my.salesforce.com",
            "id": "00Dxx0000006IYJ",
            "user": {
                "id": "005xx000001X8Uz",
                "on_behalf_of_user_id": None,
                "username": "user@example.tld",
            },
        },
    }


def test_logging(capsys: CaptureFixture[str]):
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


def test_invalid_function():
    expected_message = r"Function failed to load! File not found: .+$"

    with pytest.raises(RuntimeError, match=expected_message):
        invoke_function("tests/fixtures/invalid_function_missing_module")

    # Remove the custom `tracebacklimit` set by the app `lifespan`'s error handling,
    # otherwise traceback output for later tests will be affected too.
    del sys.tracebacklimit


def test_cloud_event_headers_missing(capsys: CaptureFixture[str]):
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


def test_cloud_event_body_not_json(capsys: CaptureFixture[str]):
    response = invoke_function("tests/fixtures/basic", content="Not json")

    expected_message = "Could not parse CloudEvent: Data payload is not valid JSON: unexpected character: line 1 column 1 (char 0)"
    assert response.status_code == 400
    assert response.headers.get("Content-Type") == "application/json"
    assert response.json() == expected_message

    output = capsys.readouterr()
    assert output.out == f'level=error msg="{expected_message}"\n'
    assert output.err == ""


def test_function_raises_exception_at_runtime(capsys: CaptureFixture[str]):
    response = invoke_function("tests/fixtures/raises_exception_at_runtime")

    expected_message = "Exception occurred whilst executing function: ZeroDivisionError: division by zero"
    assert response.status_code == 500
    assert response.headers.get("Content-Type") == "application/json"
    assert response.json() == expected_message

    output = capsys.readouterr()
    assert output.out.endswith(
        rf"""
    return 1 / 0
           ~~^~~
ZeroDivisionError: division by zero
invocationId=56ff961b-61b9-4310-a159-1f997221ccfb level=error msg="{expected_message}"
"""
    )
    assert output.err == ""


def test_return_value_not_serializable(capsys: CaptureFixture[str]):
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


def test_internal_error(capsys: CaptureFixture[str]):
    with patch(
        "salesforce_functions._internal.app.SalesforceFunctionsCloudEvent.from_http",
        side_effect=ValueError("Some internal error"),
    ):
        response = invoke_function(
            "tests/fixtures/basic", raise_server_exceptions=False
        )

    expected_message = f"Internal error: ValueError: Some internal error"
    assert response.status_code == 500
    assert response.headers.get("Content-Type") == "application/json"
    assert response.json() == expected_message

    output = capsys.readouterr()
    assert output.out == f'level=error msg="{expected_message}"\n'
    assert output.err == ""


def test_nonexistent_path():
    with patch.dict(os.environ, {"FUNCTION_PROJECT_PATH": "tests/fixtures/basic"}):
        with TestClient(app) as client:
            response = client.post(  # pyright: ignore [reportUnknownMemberType]
                "/nonexistent"
            )

    assert response.status_code == 404


def test_unsupported_http_method_get():
    with patch.dict(os.environ, {"FUNCTION_PROJECT_PATH": "tests/fixtures/basic"}):
        with TestClient(app) as client:
            response = client.get("/")  # pyright: ignore [reportUnknownMemberType]

    assert response.status_code == 405


def test_unsupported_http_method_delete():
    with patch.dict(os.environ, {"FUNCTION_PROJECT_PATH": "tests/fixtures/basic"}):
        with TestClient(app) as client:
            response = client.delete("/")  # pyright: ignore [reportUnknownMemberType]

    assert response.status_code == 405
