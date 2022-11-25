from dataclasses import dataclass

__all__ = [
    "InnerSalesforceRestApiError",
    "DataApiError",
    "MissingIdFieldError",
    "SalesforceRestApiError",
    "UnexpectedRestApiResponsePayload",
]


@dataclass(frozen=True, slots=True)
class InnerSalesforceRestApiError:
    """An error returned from the Salesforce REST API."""

    message: str
    error_code: str
    fields: list[str]


class DataApiError(Exception):
    """Base class for Data API exceptions"""


@dataclass(frozen=True, slots=True)
class SalesforceRestApiError(DataApiError):
    """Raised when the Salesforce REST API signalled error(s)."""

    api_errors: list[InnerSalesforceRestApiError]


@dataclass(frozen=True, slots=True)
class MissingIdFieldError(DataApiError):
    """Raised when the given Record must contain an "Id" field, but none was found."""


@dataclass(frozen=True, slots=True)
class UnexpectedRestApiResponsePayload(DataApiError):
    """Raised when the Salesforce REST API returned an unexpected payload."""
