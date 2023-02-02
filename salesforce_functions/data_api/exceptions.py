from dataclasses import dataclass

# The order in `__all__` is the in which pdoc3 will display the classes in the docs.
__all__ = [
    "DataApiError",
    "SalesforceRestApiError",
    "InnerSalesforceRestApiError",
    "MissingFieldError",
    "ClientError",
    "UnexpectedRestApiResponsePayload",
]


class DataApiError(Exception):
    """Base class for Data API exceptions."""


@dataclass(frozen=True, kw_only=True, slots=True)
class SalesforceRestApiError(DataApiError):
    """Raised when the Salesforce REST API signalled error(s)."""

    api_errors: list["InnerSalesforceRestApiError"]
    """A list of one or more errors returned from Salesforce REST API."""

    def __str__(self) -> str:
        errors_list = "\n---\n".join(str(error) for error in self.api_errors)
        return (
            f"Salesforce REST API reported the following error(s):\n---\n{errors_list}"
        )


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

    This will be empty for errors that aren't related to a specific field.
    """

    def __str__(self) -> str:
        # The error message includes the field names, so `self.fields` is intentionally not
        # included, as the string representation is for human not programmatic consumption.
        return f"{self.error_code} error:\n{self.message}"


class MissingFieldError(DataApiError):
    """Raised when the given `Record` must contain a field, but no such field was found."""


class ClientError(DataApiError):
    """Raised when the API request failed due to a connection error, timeout, or malformed HTTP response."""


class UnexpectedRestApiResponsePayload(DataApiError):
    """Raised when the Salesforce REST API returned an unexpected payload."""
