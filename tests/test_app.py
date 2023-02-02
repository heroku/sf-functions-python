import os
import re
import sys
from typing import Any
from unittest.mock import patch

import orjson
import pytest
from pytest import CaptureFixture
from starlette.testclient import TestClient

from salesforce_functions._internal.app import PROJECT_PATH_ENV_VAR, asgi_app

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

    extra_info: dict[str, Any] = orjson.loads(response.headers["x-extra-info"])
    assert extra_info == {
        "requestId": "n/a",
        "source": "n/a",
        "statusCode": 200,
    }

    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == ""


def test_empty_payload_and_response(capsys: CaptureFixture[str]) -> None:
    response = invoke_function("tests/fixtures/basic")
    assert response.status_code == 200
    assert response.headers.get("Content-Type") == "application/json"
    assert response.json() is None

    extra_info: dict[str, Any] = orjson.loads(response.headers["x-extra-info"])
    exec_time_ms: int = extra_info.pop("execTimeMs")
    assert extra_info == {
        "requestId": "00DJS0000000123ABC-d75b3b6ece5011dcabbed4-3c6f7179",
        "source": "urn:event:from:salesforce/JS/56.0/00DJS0000000123ABC/apex/ExampleClass:example_function():7",
        "statusCode": 200,
    }
    assert 0 <= exec_time_ms < 1000

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
        "id": "00DJS0000000123ABC-d75b3b6ece5011dcabbed4-3c6f7179",
        "source": "urn:event:from:salesforce/JS/56.0/00DJS0000000123ABC/apex/ExampleClass:example_function():7",
        "time": "2023-01-19T10:09:12.476684+00:00",
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
        "id": "00DJS0000000123ABC-d75b3b6ece5011dcabbed4-3c6f7179",
        "source": "urn:event:from:salesforce/JS/56.0/00DJS0000000123ABC/apex/ExampleClass:example_function():7",
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
            "id": "00DJS0000000123ABC",
            "user": {
                "id": "005JS000000H123",
                "on_behalf_of_user_id": "005JS000000H456",
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
            "id": "00DJS0000000123ABC",
            "user": {
                "id": "005JS000000H123",
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
invocationId=00DJS0000000123ABC-d75b3b6ece5011dcabbed4-3c6f7179 level=info msg="Info message"
invocationId=00DJS0000000123ABC-d75b3b6ece5011dcabbed4-3c6f7179 level=warning msg="Warning message"
invocationId=00DJS0000000123ABC-d75b3b6ece5011dcabbed4-3c6f7179 level=error msg="Error message"
invocationId=00DJS0000000123ABC-d75b3b6ece5011dcabbed4-3c6f7179 level=critical msg="Critical message"
record_id=12345 invocationId=00DJS0000000123ABC-d75b3b6ece5011dcabbed4-3c6f7179 level=info msg="Info message with custom metadata"
"""  # noqa: E501
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


def test_invalid_config() -> None:
    expected_message = (
        r"Unable to load function: Didn't find a project.toml file at .+\.$"
    )

    try:
        with pytest.raises(RuntimeError, match=expected_message):
            invoke_function("tests/fixtures/project_toml_file_missing")

        # The error handling in `app._lifespan()` sets a custom `sys.tracebacklimit` to
        # truncate the traceback, to improve readability of the error message.
        assert getattr(sys, "tracebacklimit", None) == 0
    finally:
        try:
            # Prevent the traceback output in later tests from being truncated too.
            del sys.tracebacklimit
        except AttributeError:
            pass


def test_invalid_function() -> None:
    expected_message = r"Unable to load function: Didn't find a main.py file at .+\.$"

    try:
        with pytest.raises(RuntimeError, match=expected_message):
            invoke_function("tests/fixtures/invalid_missing_main_py")

        # The error handling in `app._lifespan()` sets a custom `sys.tracebacklimit` to
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
        "Couldn't parse CloudEvent: Content-Type must be 'application/json' not ''"
    )
    assert response.status_code == 400
    assert response.headers.get("Content-Type") == "application/json"
    assert response.json() == expected_message

    extra_info: dict[str, Any] = orjson.loads(response.headers["x-extra-info"])
    stack: str = extra_info.pop("stack")
    assert extra_info == {
        "isFunctionError": False,
        "requestId": "n/a",
        "source": "n/a",
        "statusCode": 400,
    }
    assert re.fullmatch(
        r"""Traceback \(most recent call last\):
  .+
salesforce_functions._internal.cloud_event.CloudEventError: Content-Type must be 'application/json' not ''
""",
        stack,
        flags=re.DOTALL,
    )

    output = capsys.readouterr()
    assert output.out == f'level=error msg="{expected_message}"\n'
    assert output.err == ""


def test_cloud_event_body_not_json(capsys: CaptureFixture[str]) -> None:
    response = invoke_function("tests/fixtures/basic", content="Not json")

    expected_message = (
        "Couldn't parse CloudEvent: Data payload isn't valid JSON:"
        " unexpected character: line 1 column 1 (char 0)"
    )
    assert response.status_code == 400
    assert response.headers.get("Content-Type") == "application/json"
    assert response.json() == expected_message

    extra_info: dict[str, Any] = orjson.loads(response.headers["x-extra-info"])
    stack: str = extra_info.pop("stack")
    assert extra_info == {
        "isFunctionError": False,
        "requestId": "n/a",
        "source": "n/a",
        "statusCode": 400,
    }
    assert re.fullmatch(
        r"""Traceback \(most recent call last\):
  .+
salesforce_functions._internal.cloud_event.CloudEventError: Data payload isn't valid JSON: .+
""",
        stack,
        flags=re.DOTALL,
    )

    output = capsys.readouterr()
    assert output.out == f'level=error msg="{expected_message}"\n'
    assert output.err == ""


def test_function_raises_exception_at_runtime(capsys: CaptureFixture[str]) -> None:
    assert not hasattr(sys, "tracebacklimit"), (
        "A custom `sys.tracebacklimit` is still defined but should not be, otherwise it"
        " will affect this test. Check earlier tests aren't missing a cleanup step."
    )

    response = invoke_function("tests/fixtures/raises_exception_at_runtime")

    expected_message = "Exception occurred while executing function: ZeroDivisionError: division by zero"
    assert response.status_code == 500
    assert response.headers.get("Content-Type") == "application/json"
    assert response.json() == expected_message

    extra_info: dict[str, Any] = orjson.loads(response.headers["x-extra-info"])
    exec_time_ms: int = extra_info.pop("execTimeMs")
    stack: str = extra_info.pop("stack")
    assert extra_info == {
        "isFunctionError": True,
        "requestId": "00DJS0000000123ABC-d75b3b6ece5011dcabbed4-3c6f7179",
        "source": "urn:event:from:salesforce/JS/56.0/00DJS0000000123ABC/apex/ExampleClass:example_function():7",
        "statusCode": 500,
    }
    assert 0 <= exec_time_ms < 1000
    assert re.fullmatch(
        r"""Traceback \(most recent call last\):
  File ".+app.py", line \d+, in _handle_function_invocation
    function_result = await function\(event, context\)
  .+
ZeroDivisionError: division by zero
""",
        stack,
        flags=re.DOTALL,
    )

    output = capsys.readouterr()
    assert re.fullmatch(
        rf"""Traceback \(most recent call last\):
  File ".+app.py", line \d+, in _handle_function_invocation
    function_result = await function\(event, context\)
  .+
ZeroDivisionError: division by zero
invocationId=00DJS0000000123ABC-d75b3b6ece5011dcabbed4-3c6f7179 level=error msg="{expected_message}"
""",
        output.out,
        flags=re.DOTALL,
    )
    assert output.err == ""


def test_return_value_not_serializable(capsys: CaptureFixture[str]) -> None:
    response = invoke_function("tests/fixtures/return_value_not_serializable")

    expected_message = "Function return value can't be serialized: TypeError: Type is not JSON serializable: set"
    assert response.status_code == 500
    assert response.headers.get("Content-Type") == "application/json"
    assert response.json() == expected_message

    extra_info: dict[str, Any] = orjson.loads(response.headers["x-extra-info"])
    exec_time_ms: int = extra_info.pop("execTimeMs")
    stack: str = extra_info.pop("stack")
    assert extra_info == {
        "isFunctionError": True,
        "requestId": "00DJS0000000123ABC-d75b3b6ece5011dcabbed4-3c6f7179",
        "source": "urn:event:from:salesforce/JS/56.0/00DJS0000000123ABC/apex/ExampleClass:example_function():7",
        "statusCode": 500,
    }
    assert 0 <= exec_time_ms < 1000
    assert re.fullmatch(
        r"""Traceback \(most recent call last\):
  .+
TypeError: Type is not JSON serializable: set
""",
        stack,
        flags=re.DOTALL,
    )

    output = capsys.readouterr()
    assert (
        output.out
        == f'invocationId=00DJS0000000123ABC-d75b3b6ece5011dcabbed4-3c6f7179 level=error msg="{expected_message}"\n'
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
    assert response.status_code == 503
    assert response.headers.get("Content-Type") == "application/json"
    assert response.json() == expected_message

    extra_info: dict[str, Any] = orjson.loads(response.headers["x-extra-info"])
    stack: str = extra_info.pop("stack")
    assert extra_info == {
        "isFunctionError": False,
        "requestId": "n/a",
        "source": "n/a",
        "statusCode": 503,
    }
    assert re.fullmatch(
        r"""Traceback \(most recent call last\):
  .+
ValueError: Some internal error
""",
        stack,
        flags=re.DOTALL,
    )

    output = capsys.readouterr()
    assert re.fullmatch(
        rf"""Traceback \(most recent call last\):
  .+
ValueError: Some internal error
level=error msg="{expected_message}"
""",
        output.out,
        flags=re.DOTALL,
    )
    assert output.err == ""


def test_nonexistent_path() -> None:
    with patch.dict(os.environ, {PROJECT_PATH_ENV_VAR: "tests/fixtures/basic"}):
        with TestClient(asgi_app) as client:
            response = client.post("/nonexistent")

    assert response.status_code == 404


def test_unsupported_http_method_get() -> None:
    with patch.dict(os.environ, {PROJECT_PATH_ENV_VAR: "tests/fixtures/basic"}):
        with TestClient(asgi_app) as client:
            response = client.get("/")

    assert response.status_code == 405


def test_unsupported_http_method_delete() -> None:
    with patch.dict(os.environ, {PROJECT_PATH_ENV_VAR: "tests/fixtures/basic"}):
        with TestClient(asgi_app) as client:
            response = client.delete("/")

    assert response.status_code == 405
