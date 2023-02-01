import re
from pathlib import Path

import pytest

from salesforce_functions._internal.config import (
    MINIMUM_SALESFORCE_API_MAJOR_VERSION,
    Config,
    ConfigError,
    load_config,
)


def test_basic_config() -> None:
    fixture = Path("tests/fixtures/basic")
    config = load_config(fixture)
    assert config == Config(salesforce_api_version="56.0")


def test_project_toml_api_version_at_minimum() -> None:
    fixture = Path("tests/fixtures/project_toml_api_version_at_minimum")
    config = load_config(fixture)
    assert config == Config(
        salesforce_api_version=f"{MINIMUM_SALESFORCE_API_MAJOR_VERSION}.0"
    )


def test_project_toml_api_version_triple_digits() -> None:
    """Test that the minimum version check isn't doing naive string comparison."""
    fixture = Path("tests/fixtures/project_toml_api_version_triple_digits")
    config = load_config(fixture)
    assert config == Config(salesforce_api_version="123.0")


def test_template_config() -> None:
    fixture = Path("tests/fixtures/template")
    config = load_config(fixture)
    assert config == Config(salesforce_api_version="56.0")


def test_project_toml_file_missing() -> None:
    fixture = Path("tests/fixtures/project_toml_file_missing")
    absolute_project_toml_path = fixture.resolve().joinpath("project.toml")
    expected_message = rf"Didn't find a project\.toml file at {re.escape(str(absolute_project_toml_path))}\.$"

    with pytest.raises(ConfigError, match=expected_message):
        load_config(fixture)


def test_project_toml_invalid_unicode() -> None:
    fixture = Path("tests/fixtures/project_toml_invalid_unicode")
    expected_message = r"Couldn't read project\.toml: UnicodeDecodeError: .+"

    with pytest.raises(ConfigError, match=expected_message):
        load_config(fixture)


def test_project_toml_invalid_toml() -> None:
    fixture = Path("tests/fixtures/project_toml_invalid_toml")
    expected_message = (
        r"The project\.toml file isn't valid TOML: Expected '=' after a key .+"
    )

    with pytest.raises(ConfigError, match=expected_message):
        load_config(fixture)


def test_project_toml_salesforce_table_missing() -> None:
    fixture = Path("tests/fixtures/project_toml_salesforce_table_missing")
    expected_message = (
        r"The project\.toml file is missing the required '\[com\.salesforce\]' table\.$"
    )

    with pytest.raises(ConfigError, match=expected_message):
        load_config(fixture)


def test_project_toml_salesforce_table_wrong_type() -> None:
    fixture = Path("tests/fixtures/project_toml_salesforce_table_wrong_type")
    expected_message = (
        r"The project\.toml file is missing the required '\[com\.salesforce\]' table\.$"
    )

    with pytest.raises(ConfigError, match=expected_message):
        load_config(fixture)


def test_project_toml_api_version_missing() -> None:
    fixture = Path("tests/fixtures/project_toml_api_version_missing")
    expected_message = (
        r"The project\.toml file is missing the required"
        r" 'com\.salesforce\.salesforce-api-version' key\.$"
    )

    with pytest.raises(ConfigError, match=expected_message):
        load_config(fixture)


def test_project_toml_api_version_wrong_type() -> None:
    fixture = Path("tests/fixtures/project_toml_api_version_wrong_type")
    expected_message = r"The 'com\.salesforce\.salesforce-api-version' key in project\.toml must be a string\.$"

    with pytest.raises(ConfigError, match=expected_message):
        load_config(fixture)


def test_project_toml_api_version_invalid() -> None:
    fixture = Path("tests/fixtures/project_toml_api_version_invalid")
    expected_message = (
        r"'55' isn't a valid Salesforce REST API version\. Update the 'salesforce-api-version'"
        r" key in project\.toml to a version that uses the form 'X\.Y', such as '56.0'\.$"
    )

    with pytest.raises(ConfigError, match=expected_message):
        load_config(fixture)


def test_project_toml_api_version_too_old() -> None:
    fixture = Path("tests/fixtures/project_toml_api_version_too_old")
    expected_message = (
        r"Salesforce REST API version '52\.1' isn't supported\."
        r" Update the 'salesforce-api-version' key in project\.toml to '53\.0' or later\.$"
    )

    with pytest.raises(ConfigError, match=expected_message):
        load_config(fixture)
