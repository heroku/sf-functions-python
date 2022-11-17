import sys
from pathlib import Path

import pytest
from pytest import CaptureFixture

from salesforce_functions.__version__ import __version__
from salesforce_functions._internal.cli import main


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


def test_check_subcommand_valid_function(capsys: CaptureFixture[str]) -> None:
    fixture = "tests/fixtures/basic"

    exit_code = main(args=["check", fixture])
    assert exit_code == 0

    output = capsys.readouterr()
    assert output.err == ""
    assert output.out == "Checking function...\n\nFunction passed validation\n"


def test_check_subcommand_invalid_function(capsys: CaptureFixture[str]) -> None:
    fixture = "tests/fixtures/invalid_function_missing_module"
    absolute_function_path = Path(fixture).resolve().joinpath("main.py")

    exit_code = main(args=["check", fixture])
    assert exit_code == 1

    output = capsys.readouterr()
    assert output.out == "Checking function...\n\n"
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


def test_serve_subcommand_default_options(capsys: CaptureFixture[str]) -> None:
    # We have to use an invalid function fixture, otherwise the server would not exit.
    fixture = "tests/fixtures/invalid_function_missing_module"

    with pytest.raises(SystemExit):
        main(args=["serve", fixture])

    # Remove the custom `tracebacklimit` set by the app `lifespan`'s error handling,
    # otherwise traceback output for later tests will be affected too.
    del sys.tracebacklimit

    output = capsys.readouterr()
    # Uvicorn's startup logs are different when only using one worker, and as such the
    # "Uvicorn running on http://localhost:8080" message isn't in the output at this point,
    # so we can't check the default host/port, only the other options.
    number_of_workers = output.err.count("Started server process")
    assert number_of_workers == 1


# TODO: Fix upstream: https://github.com/encode/uvicorn/issues/1115 (W-12034429)
@pytest.mark.skip(
    reason="uvicorn never fully shuts down when using multiple workers, so the test will hang"
)
def test_serve_subcommand_custom_options(capsys: CaptureFixture[str]) -> None:
    # We have to use an invalid function fixture, otherwise the server would not exit.
    fixture = "tests/fixtures/invalid_function_missing_module"

    with pytest.raises(SystemExit):
        main(
            args=[
                "serve",
                "--host",
                "0.0.0.0",
                "--port",
                "12345",
                "--workers",
                "5",
                fixture,
            ]
        )

    # Remove the custom `tracebacklimit` set by the app `lifespan`'s error handling,
    # otherwise traceback output for later tests will be affected too.
    del sys.tracebacklimit

    output = capsys.readouterr()
    # The host/port is only logged by uvicorn when running multiple workers,
    # so it's easier to test all options in the same test.
    assert "Uvicorn running on http://0.0.0.0:12345" in output.err
    number_of_workers = output.err.count("Started server process")
    assert number_of_workers == 5


def test_serve_subcommand_invalid_function(capsys: CaptureFixture[str]) -> None:
    fixture = "tests/fixtures/invalid_function_missing_module"
    absolute_function_path = Path(fixture).resolve().joinpath("main.py")

    with pytest.raises(SystemExit) as exc_info:
        main(args=["serve", fixture])

    # Remove the custom `tracebacklimit` set by the app `lifespan`'s error handling,
    # otherwise traceback output for later tests will be affected too.
    del sys.tracebacklimit

    exit_code = exc_info.value.code
    assert exit_code == 3

    output = capsys.readouterr()
    assert output.out == ""
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
