from dataclasses import dataclass

from .data_api import DataAPI


@dataclass(frozen=True, slots=True)
class User:
    """Information about the invoking Salesforce user."""

    id: str
    """The user's ID."""
    username: str
    """The name of the user."""
    on_behalf_of_user_id: str | None
    """The ID of the user on whose behalf this user is operating."""


@dataclass(frozen=True, slots=True)
class Org:
    """Information about the invoking Salesforce organization and user."""

    id: str
    """The Salesforce organization ID."""
    base_url: str
    """The base URL of the Salesforce organization."""
    domain_url: str
    """The domain URL of the Salesforce organization."""
    # TODO: This version is the version from pyproject.toml, not the cloud event.
    # Should it have a clearer name/be omitted? Should we surface the version from the cloudevent?
    api_version: str
    """The API version the Salesforce organization is currently using."""
    data_api: DataAPI
    """An initialized data API client instance for interacting with data in the org."""
    user: User
    """The currently logged in user."""


@dataclass(frozen=True, slots=True)
class Context:
    """Information relating to the function and the Salesforce org with which it is associated."""

    org: Org | None
    """Information about the invoking Salesforce organization and user."""
