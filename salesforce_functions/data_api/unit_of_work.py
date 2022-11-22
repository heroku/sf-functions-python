from ._requests import (
    CreateRecordRestApiRequest,
    DeleteRecordRestApiRequest,
    RestApiRequest,
    UpdateRecordRestApiRequest,
)
from .record import Record
from .reference_id import ReferenceId

__all__ = ["UnitOfWork"]


class UnitOfWork:
    """
    Represents a UnitOfWork.

    After registering all operations, it can be submitted via the commit_unit_of_work method of DataApi.
    """

    def __init__(self) -> None:
        self._sub_requests: dict[ReferenceId, RestApiRequest[str]] = {}
        self._next_reference_id = 0

    def register_create(self, record: Record) -> ReferenceId:
        """
        Register a record creation for the UnitOfWork.

        Returns a ReferenceId that can be used to refer to the created record in subsequent operations in this
        UnitOfWork.
        """
        return self._register(CreateRecordRestApiRequest(record))

    def register_update(self, record: Record) -> ReferenceId:
        """
        Register a record update for the UnitOfWork.

        Returns a ReferenceId that can be used to refer to the updated record in subsequent operations in this
        UnitOfWork.
        """
        return self._register(UpdateRecordRestApiRequest(record))

    def register_delete(self, object_type: str, record_id: str) -> ReferenceId:
        """
        Register a deletion of an existing record of the given type and id.
        """
        return self._register(DeleteRecordRestApiRequest(object_type, record_id))

    def _register(self, request: RestApiRequest[str]) -> ReferenceId:
        reference_id = ReferenceId("referenceId" + str(self._next_reference_id))
        self._next_reference_id += 1

        self._sub_requests[reference_id] = request
        return reference_id
