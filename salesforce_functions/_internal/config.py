import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

if sys.version_info < (3, 11):
    # `tomllib` was only added to the stdlib in Python 3.11, so for older Python
    # versions we use the third party `tomli` package, which has an identical API.
    import tomli as tomllib  # pragma: no-cover-python-gte-311
else:
    import tomllib  # pragma: no-cover-python-lt-311

MINIMUM_SALESFORCE_API_MAJOR_VERSION = 53


@dataclass(frozen=True, kw_only=True, slots=True)
class Config:
    """The function's configuration."""

    salesforce_api_version: str
    """The requested Salesforce REST API version (for example '56.0')."""


def load_config(project_path: Path) -> Config:
    """Load a function's configuration from its project.toml file."""
    project_toml_path = project_path.joinpath("project.toml").resolve()

    if not project_toml_path.is_file():
        raise ConfigError(f"A project.toml file was not found at: {project_toml_path}")

    try:
        with project_toml_path.open(mode="rb") as file:
            project_toml = tomllib.load(file)
    except tomllib.TOMLDecodeError as e:
        raise ConfigError(f"project.toml is not valid TOML: {e}") from e
    except Exception as e:  # e.g.: OSError, UnicodeDecodeError.
        raise ConfigError(
            f"Could not read project.toml: {e.__class__.__name__}: {e}"
        ) from e

    try:
        salesforce_table: dict[str, Any] = project_toml["com"]["salesforce"]
        salesforce_api_version = salesforce_table.get("salesforce-api-version")
    except (AttributeError, KeyError, ValueError) as e:
        raise ConfigError(
            "project.toml is missing the required '[com.salesforce]' table."
        ) from e

    if salesforce_api_version is None:
        raise ConfigError(
            "project.toml is missing the required 'com.salesforce.salesforce-api-version' key."
        )

    if not isinstance(salesforce_api_version, str):
        raise ConfigError(
            "The 'com.salesforce.salesforce-api-version' key in project.toml must be a string."
        )

    match = re.match(r"(?P<major_version>\d+)\.\d+$", salesforce_api_version)

    if not match:
        raise ConfigError(
            f"'{salesforce_api_version}' is not a valid Salesforce REST API version. "
            "Update 'salesforce-api-version' in project.toml to a version of form 'X.Y'."
        )

    if int(match.group("major_version")) < MINIMUM_SALESFORCE_API_MAJOR_VERSION:
        raise ConfigError(
            f"Salesforce REST API version '{salesforce_api_version}' is not supported. Update"
            f" 'salesforce-api-version' in project.toml to '{MINIMUM_SALESFORCE_API_MAJOR_VERSION}.0' or newer."
        )

    return Config(salesforce_api_version=salesforce_api_version)


class ConfigError(Exception):
    """There was an error loading the project config or it failed validation."""
