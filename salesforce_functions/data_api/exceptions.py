from dataclasses import dataclass

# The order in `__all__` is the in which pdoc3 will display the classes in the docs.
__all__ = [
    "DataApiError",
    "SalesforceRestApiError",
    "InnerSalesforceRestApiError",
    "MissingIdFieldError",
    "UnexpectedRestApiResponsePayload",
]


class DataApiError(Exception):
    """Base class for Data API exceptions."""


@dataclass(frozen=True, kw_only=True, slots=True)
class SalesforceRestApiError(DataApiError):
    """Raised when the Salesforce REST API signalled error(s)."""

    api_errors: list["InnerSalesforceRestApiError"]
    """A list of one or more errors returned from the Salesforce REST API."""


@dataclass(frozen=True, kw_only=True, slots=True)
class InnerSalesforceRestApiError:
    """An error returned from the Salesforce REST API."""

    message: str
    """The description of this error."""
    error_code: str
    """The error code for this error."""
    fields: list[str]
    """
    The field names where the error occurred.

    This will be empty for errors that are not related to a specific field.
    """


@dataclass(frozen=True, kw_only=True, slots=True)
class MissingIdFieldError(DataApiError):
    """Raised when the given Record must contain an `Id` field, but none was found."""


@dataclass(frozen=True, kw_only=True, slots=True)
class UnexpectedRestApiResponsePayload(DataApiError):
    """Raised when the Salesforce REST API returned an unexpected payload."""
