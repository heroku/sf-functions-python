import os
import sys
from importlib.metadata import distribution
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from pytest import CaptureFixture

from salesforce_functions.__version__ import __version__
from salesforce_functions._internal.cli import PROGRAM_NAME, main
from salesforce_functions._internal.config import PROJECT_PATH_ENV_VAR


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


def test_check_subcommand_invalid_function(capsys: CaptureFixture[str]) -> None:
    fixture = "tests/fixtures/invalid_function_missing_module"
    absolute_function_path = Path(fixture).resolve().joinpath("main.py")

    exit_code = main(args=["check", fixture])
    assert exit_code == 1

    output = capsys.readouterr()
    assert output.out == ""
    assert (
        output.err
        == f"Error: Function failed validation! File not found: {absolute_function_path}\n"
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
            "salesforce_functions._internal.app:app",
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
            "salesforce_functions._internal.app:app",
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


def test_serve_subcommand_invalid_function(capsys: CaptureFixture[str]) -> None:
    fixture = "tests/fixtures/invalid_function_missing_module"
    absolute_function_path = Path(fixture).resolve().joinpath("main.py")

    with pytest.raises(SystemExit) as exc_info:
        main(args=["serve", fixture])

    # The error handling in `app.lifespan()` sets a custom `sys.tracebacklimit` to
    # improve readability of the error message. This must be cleaned up otherwise
    # traceback output for later tests will be affected too.
    assert getattr(sys, "tracebacklimit") == 0
    del sys.tracebacklimit

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
ERROR:    RuntimeError: Function failed to load! File not found: {absolute_function_path}

ERROR:    Application startup failed. Exiting.
"""
    )


def test_version_subcommand(capsys: CaptureFixture[str]) -> None:
    exit_code = main(args=["version"])
    assert exit_code == 0

    output = capsys.readouterr()
    assert output.err == ""
    assert output.out == f"{__version__}\n"
