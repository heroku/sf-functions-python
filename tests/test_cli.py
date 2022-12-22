import os
import subprocess
import sys
from importlib.metadata import distribution
from pathlib import Path
from typing import Any
from unittest.mock import patch

import httpx
import pytest
from pytest import CaptureFixture

from salesforce_functions.__version__ import __version__
from salesforce_functions._internal.app import PROJECT_PATH_ENV_VAR
from salesforce_functions._internal.cli import (
    ASGI_APP_IMPORT_STRING,
    PROGRAM_NAME,
    main,
)


def test_program_name_matches_package_entry_points() -> None:
    package_script_names = (
        distribution("salesforce_functions")
        .entry_points.select(group="console_scripts")
        .names
    )
    assert PROGRAM_NAME in package_script_names


def test_base_help(capsys: CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(args=["--help"])

    exit_code = exc_info.value.code
    assert exit_code == 0

    output = capsys.readouterr()
    assert (
        output.out
        == r"""usage: sf-functions-python [-h] {check,serve,version} ...

Salesforce Functions Python Runtime

options:
  -h, --help            show this help message and exit

subcommands:
  {check,serve,version}
    check               Checks that a function project is configured correctly
    serve               Serves a function project via HTTP
    version             Prints the version of the Python Functions Runtime
"""
    )


def test_missing_subcommand(capsys: CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(args=[])

    exit_code = exc_info.value.code
    assert exit_code == 2

    output = capsys.readouterr()
    assert "error: the following arguments are required: subcommand" in output.err


def test_check_subcommand_help(capsys: CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(args=["check", "--help"])

    exit_code = exc_info.value.code
    assert exit_code == 0

    output = capsys.readouterr()
    assert (
        output.out
        == r"""usage: sf-functions-python check [-h] <project-path>

positional arguments:
  <project-path>  The directory that contains the function

options:
  -h, --help      show this help message and exit
"""
    )


def test_check_subcommand_missing_project_path(capsys: CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(args=["check"])

    exit_code = exc_info.value.code
    assert exit_code == 2

    output = capsys.readouterr()
    assert "error: the following arguments are required: <project-path>" in output.err


def test_check_subcommand_valid_function(capsys: CaptureFixture[str]) -> None:
    fixture = "tests/fixtures/basic"

    exit_code = main(args=["check", fixture])
    assert exit_code == 0

    output = capsys.readouterr()
    assert output.err == ""
    assert output.out == "Function passed validation\n"


def test_check_subcommand_invalid_config(capsys: CaptureFixture[str]) -> None:
    fixture = "tests/fixtures/project_toml_file_missing"
    project_toml_path = Path(fixture).resolve().joinpath("project.toml")

    exit_code = main(args=["check", fixture])
    assert exit_code == 1

    output = capsys.readouterr()
    assert output.out == ""
    assert (
        output.err
        == f"Function failed validation: A project.toml file was not found at: {project_toml_path}\n"
    )


def test_check_subcommand_invalid_function(capsys: CaptureFixture[str]) -> None:
    fixture = "tests/fixtures/invalid_missing_main_py"
    main_py_path = Path(fixture).resolve().joinpath("main.py")

    exit_code = main(args=["check", fixture])
    assert exit_code == 1

    output = capsys.readouterr()
    assert output.out == ""
    assert (
        output.err
        == f"Function failed validation: A main.py file was not found at: {main_py_path}\n"
    )


def test_serve_subcommand_help(capsys: CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(args=["serve", "--help"])

    exit_code = exc_info.value.code
    assert exit_code == 0

    output = capsys.readouterr()
    assert (
        output.out
        == r"""usage: sf-functions-python serve [-h] [--host HOST] [-p PORT] [-w WORKERS]
                                 <project-path>

positional arguments:
  <project-path>        The directory that contains the function

options:
  -h, --help            show this help message and exit
  --host HOST           The host on which the web server should bind (default:
                        localhost)
  -p PORT, --port PORT  The port on which the web server should listen
                        (default: 8080)
  -w WORKERS, --workers WORKERS
                        The number of worker processes (default: 1)
"""
    )


def test_serve_subcommand_missing_project_path(capsys: CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(args=["serve"])

    exit_code = exc_info.value.code
    assert exit_code == 2

    output = capsys.readouterr()
    assert "error: the following arguments are required: <project-path>" in output.err


def test_serve_subcommand_default_options(capsys: CaptureFixture[str]) -> None:
    project_path = "path/to/function"
    # Still a relative path, but with the path separators adjusted for the current OS.
    normalised_path = str(Path(project_path))

    def check_project_path_env_var(*_args: Any, **_kwargs: Any) -> None:
        assert os.environ.get(PROJECT_PATH_ENV_VAR) == normalised_path

    with patch(
        "uvicorn.run", side_effect=check_project_path_env_var
    ) as mock_uvicorn_run:
        main(args=["serve", project_path])

        mock_uvicorn_run.assert_called_once_with(
            ASGI_APP_IMPORT_STRING,
            host="localhost",
            port=8080,
            workers=1,
            access_log=False,
        )

    assert PROJECT_PATH_ENV_VAR not in os.environ

    output = capsys.readouterr()
    assert output.err == ""
    assert (
        output.out
        == f"Starting sf-functions-python v{__version__} in single process mode.\n"
    )


def test_serve_subcommand_custom_options(capsys: CaptureFixture[str]) -> None:
    project_path = "path/to/function"
    # Still a relative path, but with the path separators adjusted for the current OS.
    normalised_path = str(Path(project_path))

    def check_project_path_env_var(*_args: Any, **_kwargs: Any) -> None:
        assert os.environ.get(PROJECT_PATH_ENV_VAR) == normalised_path

    with patch(
        "uvicorn.run", side_effect=check_project_path_env_var
    ) as mock_uvicorn_run:
        main(
            args=[
                "serve",
                "--host",
                "0.0.0.0",
                "--port",
                "12345",
                "--workers",
                "5",
                project_path,
            ]
        )

        mock_uvicorn_run.assert_called_once_with(
            ASGI_APP_IMPORT_STRING,
            host="0.0.0.0",
            port=12345,
            workers=5,
            access_log=False,
        )

    assert PROJECT_PATH_ENV_VAR not in os.environ

    output = capsys.readouterr()
    assert output.err == ""
    assert (
        output.out
        == f"Starting sf-functions-python v{__version__} in multi-process mode (5 worker processes).\n"
    )


def test_serve_subcommand_valid_function() -> None:
    fixture = "tests/fixtures/basic"
    port = 41234

    with subprocess.Popen(
        ["python", "-m", "salesforce_functions", "serve", "--port", str(port), fixture]
    ) as server_process:
        try:
            with httpx.Client(transport=httpx.HTTPTransport(retries=5)) as client:
                # Checks that uvicorn is binding to both the IPv4 and IPv6 adapters
                # when it is binding to localhost, since clients will use either.
                headers = {"x-health-check": "true"}
                ipv4_response = client.post(f"http://127.0.0.1:{port}", headers=headers)
                ipv6_response = client.post(f"http://[::1]:{port}", headers=headers)
        finally:
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()

    # Using `Popen.terminate()` results in a non-zero exit code on Windows for some reason.
    if sys.platform == "win32":
        assert server_process.returncode == 1
    else:
        assert server_process.returncode == 0

    assert ipv4_response.status_code == 200
    assert ipv4_response.json() == "OK"

    assert ipv6_response.status_code == 200
    assert ipv6_response.json() == "OK"


def test_serve_subcommand_invalid_config(capsys: CaptureFixture[str]) -> None:
    fixture = "tests/fixtures/project_toml_file_missing"
    project_toml_path = Path(fixture).resolve().joinpath("project.toml")

    try:
        with pytest.raises(SystemExit) as exc_info:
            main(args=["serve", fixture])

        # The error handling in `app.lifespan()` sets a custom `sys.tracebacklimit` to
        # truncate the traceback, to improve readability of the error message.
        assert getattr(sys, "tracebacklimit", None) == 0
    finally:
        try:
            # Prevent the traceback output in later tests from being truncated too.
            del sys.tracebacklimit
        except AttributeError:
            pass

    exit_code = exc_info.value.code
    assert exit_code == 3

    output = capsys.readouterr()
    assert (
        output.out
        == f"Starting sf-functions-python v{__version__} in single process mode.\n"
    )
    assert output.err.endswith(
        rf"""
INFO:     Waiting for application startup.
ERROR:    RuntimeError: Unable to load function: A project.toml file was not found at: {project_toml_path}

ERROR:    Application startup failed. Exiting.
"""
    )


def test_serve_subcommand_invalid_function(capsys: CaptureFixture[str]) -> None:
    fixture = "tests/fixtures/invalid_missing_main_py"
    main_py_path = Path(fixture).resolve().joinpath("main.py")

    try:
        with pytest.raises(SystemExit) as exc_info:
            main(args=["serve", fixture])

        # The error handling in `app.lifespan()` sets a custom `sys.tracebacklimit` to
        # truncate the traceback, to improve readability of the error message.
        assert getattr(sys, "tracebacklimit", None) == 0
    finally:
        try:
            # Prevent the traceback output in later tests from being truncated too.
            del sys.tracebacklimit
        except AttributeError:
            pass

    exit_code = exc_info.value.code
    assert exit_code == 3

    output = capsys.readouterr()
    assert (
        output.out
        == f"Starting sf-functions-python v{__version__} in single process mode.\n"
    )
    assert output.err.endswith(
        rf"""
INFO:     Waiting for application startup.
ERROR:    RuntimeError: Unable to load function: A main.py file was not found at: {main_py_path}

ERROR:    Application startup failed. Exiting.
"""
    )


def test_version_subcommand(capsys: CaptureFixture[str]) -> None:
    exit_code = main(args=["version"])
    assert exit_code == 0

    output = capsys.readouterr()
    assert output.err == ""
    assert output.out == f"{__version__}\n"

    # Ensure the command output can be parsed as a semver-compatible string by the CLI and CNB.
    # This test is more restrictive than semver, but that's fine for our purposes, and saves
    # adding another dependency (which might even be using a different semver flavour anyway).
    version_parts = output.out.strip().split(".")
    assert len(version_parts) == 3
    assert all(map(lambda s: s.isdigit(), version_parts))
