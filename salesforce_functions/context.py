from dataclasses import dataclass

from .data_api import DataAPI

__all__ = ["User", "Org", "Context"]


@dataclass(frozen=True, kw_only=True, slots=True)
class User:
    """Information about the invoking Salesforce user."""

    id: str
    """
    The user's ID.

    For example: `005JS000000H123`
    """
    username: str
    """
    The username of the user.

    For example: `user@example.tld`
    """
    on_behalf_of_user_id: str | None
    """
    The ID of the user on whose behalf this user is operating.

    For example: `005JS000000H456`
    """


@dataclass(frozen=True, kw_only=True, slots=True)
class Org:
    """Information about the invoking Salesforce org and user."""

    id: str
    """
    The Salesforce org ID.

    For example: `00DJS0000000123ABC`
    """
    base_url: str
    """
    The base URL of the Salesforce org.

    For example: `https://example-base-url.my.salesforce-sites.com`
    """
    domain_url: str
    """
    The domain URL of the Salesforce org.

    For example: `https://example-domain-url.my.salesforce.com`
    """
    data_api: DataAPI
    """An initialized data API client instance for interacting with data in the org."""
    user: User
    """The currently logged in user."""


@dataclass(frozen=True, kw_only=True, slots=True)
class Context:
    """Information relating to the function and the Salesforce org with which it is associated."""

    org: Org
    """Information about the invoking Salesforce org and user."""
