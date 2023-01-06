import subprocess

import pytest

from salesforce_functions._internal.cli import PROGRAM_NAME


def test_package_main() -> None:
    process = subprocess.run(
        ["python", "-m", "salesforce_functions", "--help"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert process.returncode == 0
    assert process.stderr == ""
    assert "usage: sf-functions-python" in process.stdout


def test_package_main_non_zero_exit_code() -> None:
    with pytest.raises(subprocess.CalledProcessError) as exc_info:
        subprocess.run(
            ["python", "-m", "salesforce_functions"],
            check=True,
            capture_output=True,
            text=True,
        )

    assert exc_info.value.returncode == 2
    assert (
        "error: the following arguments are required: subcommand"
        in exc_info.value.stderr
    )


def test_entry_point_script() -> None:
    """Tests the `sf-functions-python` entry point that is used by the CLI and CNB."""
    process = subprocess.run(
        [PROGRAM_NAME, "--help"], check=True, capture_output=True, text=True
    )

    assert process.returncode == 0
    assert process.stderr == ""
    assert "usage: sf-functions-python" in process.stdout
