from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ReferenceId:
    """
    A reference id for an operation inside a unit of work.

    Used to reference results of other operations inside the same unit of work.
    """

    id: str
