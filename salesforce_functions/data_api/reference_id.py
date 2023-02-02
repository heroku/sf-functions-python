from dataclasses import dataclass

__all__ = ["ReferenceId"]


@dataclass(frozen=True, kw_only=True, slots=True)
class ReferenceId:
    """
    A reference ID for an operation inside a `UnitOfWork`.

    Used to reference results of other operations inside the same unit of work.
    """

    id: str
    """The internal identifier of this `ReferenceId`."""
