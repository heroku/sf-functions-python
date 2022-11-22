from dataclasses import dataclass, field
from typing import Any

__all__ = ["Record", "QueriedRecord", "RecordQueryResult"]


@dataclass(frozen=True, slots=True)
class Record:
    """A Salesforce record."""

    type: str
    """The Salesforce Object type."""
    fields: dict[str, Any]
    """The fields belonging to the record."""


@dataclass(frozen=True, slots=True)
class QueriedRecord(Record):
    """
    A Salesforce record that has been queried.

    Extends Record with potential sub query results that can only exist when
    a record was queried from the data API.
    """

    sub_query_results: dict[str, "RecordQueryResult"] = field(default_factory=dict)
    """Additional query results from sub queries."""


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
    records: list[QueriedRecord]
    """
    The `Record`s in this query result.

    Use `done` to determine whether there are additional records to be
    queried with `queryMore`.
    """
    next_records_url: str | None
    """The URL for the next set of records, if any."""
