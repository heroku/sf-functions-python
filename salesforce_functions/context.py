from dataclasses import dataclass

from .data_api import DataAPI

__all__ = ["User", "Org", "Context"]


@dataclass(frozen=True, kw_only=True, slots=True)
class User:
    """
    Information about the Salesforce user that invoked the function.

    When deployed to a compute environment, the function runs as the Salesforce user with the
    Cloud Integration User profile when making requests to the org, not as the actual Salesforce
    user that invoked the function. See [Update Function Permissions](https://developer.salesforce.com/docs/platform/functions/guide/permissions.html)
    for details.

    When invoked locally, the function runs as the user who executed the CLI command, with their
    credentials. See [Invoke Functions Locally](https://developer.salesforce.com/docs/platform/functions/guide/invoke-local.html).
    """  # noqa: E501 pylint: disable=line-too-long

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
    """Information about the Salesforce org and the user that invoked the function."""

    id: str
    """
    The Salesforce org ID.

    For example: `00DJS0000000123ABC`
    """
    base_url: str
    """
    The URL of the current connection to the Salesforce org.

    If [Salesforce Sites](https://help.salesforce.com/s/articleView?id=sf.sites_overview.htm&type=5)
    is enabled in the org, then the URL follows their format. The URL could also include the
    Salesforce instance, which can change if the org migrates to a new instance.

    For example: `https://example-base-url.my.salesforce-sites.com`
    """
    domain_url: str
    """
    The canonical URL of the Salesforce org.

    This URL never changes. Use this URL when making API calls to your org.

    For example: `https://example-domain-url.my.salesforce.com`
    """
    data_api: DataAPI
    """An initialized data API client instance for interacting with data in the org."""
    user: User
    """The currently logged in user."""


@dataclass(frozen=True, kw_only=True, slots=True)
class Context:
    """Information about the Salesforce org that invoked the function."""

    org: Org
    """Information about the Salesforce org and the user that invoked the function."""
