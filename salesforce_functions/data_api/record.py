from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class Record:
    """A Salesforce record."""

    type: str
    """The Salesforce Object type."""
    fields: dict[str, Any]
    """The fields belonging to the record."""


@dataclass(frozen=True, slots=True)
class RecordQueryResult:
    """The result of a record query."""

    done: bool
    """
    Indicates whether all record results have been returned.

    If true, no additional records can be retrieved from the query result.
    If false, one or more records remain to be retrieved.
    """
    total_size: int
    """
    The total number of records returned by the query.

    This is not necessarily the same number of records found in `records`.
    """
    records: list[dict[str, Any]]
    """
    The `Record`s in this query result.

    Use `done` to determine whether there are additional records to be
    queried with `queryMore`.
    """
    next_records_url: str | None
    """The URL for the next set of records, if any."""


@dataclass(frozen=True, slots=True)
class RecordModificationResult:
    """The result of a record modification such as a create, update or delete."""

    id: str
    """The ID of the modified record."""
