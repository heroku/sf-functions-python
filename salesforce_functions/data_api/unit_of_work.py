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
    Represents a `UnitOfWork`.

    A `UnitOfWork` encapsulates a set of one or more Salesforce operations that must be
    performed as a single atomic operation. Single atomic operations reduce the number of
    requests back to the org, and are more efficient when working with larger data volumes.

    First, register the create, update, or delete operations that make up the `UnitOfWork`
    using their corresponding methods, such as `register_create`. Then submit the `UnitOfWork`
    with the `commit_unit_of_work` method of `DataAPI`.

    For example:

    ```python
    from salesforce_functions import Record, UnitOfWork

    # Create a unit of work, against which multiple operations can be registered.
    unit_of_work = UnitOfWork()

    # Register a new Account for creation
    account_reference_id = unit_of_work.register_create(
        Record(
            type="Account",
            fields={
                "Name": "Example Account",
            },
        )
    )

    # Register a new Contact for creation, that references the account above.
    unit_of_work.register_create(
        Record(
            type="Contact",
            fields={
                "FirstName": "Joe",
                "LastName": "Smith",
                "AccountId": account_reference_id,
            },
        )
    )

    # Commit the unit of work, executing all of the operations registered above.
    result = await context.org.data_api.commit_unit_of_work(unit_of_work)
    ```
    """

    def __init__(self) -> None:
        self._sub_requests: dict[ReferenceId, RestApiRequest[str]] = {}
        self._next_reference_id = 0

    def register_create(self, record: Record) -> ReferenceId:
        """
        Register a record creation for the `UnitOfWork`.

        Returns a `ReferenceId` that you can use to refer to the created record in subsequent operations in this
        `UnitOfWork`.

        For example:

        ```python
        from salesforce_functions import Record, UnitOfWork

        unit_of_work = UnitOfWork()

        reference_id = unit_of_work.register_create(
            Record(
                type="Account",
                fields={
                    "Name": "Example Account",
                },
            )
        )
        ```
        """
        return self._register(CreateRecordRestApiRequest(record))

    def register_update(self, record: Record) -> ReferenceId:
        """
        Register a record update for the `UnitOfWork`.

        The given `Record` must contain an `Id` field.

        Returns a `ReferenceId` that you can use to refer to the updated record in subsequent operations in this
        `UnitOfWork`.

        For example:

        ```python
        from salesforce_functions import Record, UnitOfWork

        unit_of_work = UnitOfWork()

        reference_id = unit_of_work.register_update(
            Record(
                type="Account",
                fields={
                    "Id": "001B000001Lp1FxIAJ",
                    "Name": "New Name",
                },
            )
        )
        ```
        """
        return self._register(UpdateRecordRestApiRequest(record))

    def register_delete(self, object_type: str, record_id: str) -> ReferenceId:
        """
        Register a deletion of an existing record of the given type and ID.

        Returns a `ReferenceId` that you can use to refer to the deleted record in subsequent operations in this
        `UnitOfWork`.

        For example:

        ```python
        from salesforce_functions import UnitOfWork

        unit_of_work = UnitOfWork()

        reference_id = unit_of_work.register_delete("Account", "001B000001Lp1FxIAJ")
        ```
        """
        return self._register(DeleteRecordRestApiRequest(object_type, record_id))

    def _register(self, request: RestApiRequest[str]) -> ReferenceId:
        reference_id = ReferenceId(id="referenceId" + str(self._next_reference_id))
        self._next_reference_id += 1

        self._sub_requests[reference_id] = request
        return reference_id
