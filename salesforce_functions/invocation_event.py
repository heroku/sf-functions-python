from dataclasses import dataclass
from typing import Generic, Optional, TypeVar

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class InvocationEvent(Generic[T]):
    """
    The metadata and data payload of the event that caused the function to be invoked.
    """

    id: str
    """The unique identifier for this execution of the function."""
    type: str
    """The type of this invocation event."""
    source: str
    """
    A URI which identifies the context in which an event happened.

    Often this will include information such as the type of the event source, the
    organization publishing the event or the process that produced the event.
    """
    data: T
    """The payload of the event."""
    # TODO: Why is this optional if we reject empty content type?
    # TODO: Why do we even leak this to the user anyway?
    data_content_type: Optional[str]
    """The media type of the event `data` payload."""
    data_schema: Optional[str]
    """The schema to which the event `data` payload adheres."""
    # TODO: Switch this to `Optional[datetime]`?
    time: Optional[str]
    """
    The timestamp of when the occurrence happened.

    If the time of the occurrence cannot be determined then this attribute
    may be set to some other time (such as the current time).
    """
