from hashlib import md5

import pytest
from aiohttp import ClientSession

from salesforce_functions import (
    QueriedRecord,
    Record,
    RecordQueryResult,
    ReferenceId,
    UnitOfWork,
)
from salesforce_functions.data_api import DataAPI
from salesforce_functions.data_api.exceptions import (
    InnerSalesforceRestApiError,
    MissingIdFieldError,
    SalesforceRestApiError,
    UnexpectedRestApiResponsePayload,
)

from .utils import WIREMOCK_SERVER_URL


def new_data_api(session: ClientSession | None = None) -> DataAPI:
    return DataAPI(WIREMOCK_SERVER_URL, "53.0", "EXAMPLE-TOKEN", session=session)


@pytest.mark.requires_wiremock
async def test_unexpected_response() -> None:
    data_api = new_data_api()

    with pytest.raises(UnexpectedRestApiResponsePayload) as exception_info:
        await data_api.query("SELECT Name FROM FruitVendor__c")

    assert exception_info.value == UnexpectedRestApiResponsePayload()


@pytest.mark.requires_wiremock
async def test_query() -> None:
    data_api = new_data_api()

    result = await data_api.query("SELECT Name FROM Account")
    assert result == RecordQueryResult(
        done=True,
        total_size=5,
        records=[
            QueriedRecord("Account", {"Name": "An awesome test account"}),
            QueriedRecord("Account", {"Name": "Global Media"}),
            QueriedRecord("Account", {"Name": "Acme"}),
            QueriedRecord("Account", {"Name": "salesforce.com"}),
            QueriedRecord("Account", {"Name": "Sample Account for Entitlements"}),
        ],
        next_records_url=None,
    )


@pytest.mark.requires_wiremock
async def test_query_more() -> None:
    data_api = new_data_api()

    result = await data_api.query("SELECT RANDOM_1__c, RANDOM_2__c FROM Random__c")
    assert result.done is False
    assert result.total_size == 10000

    result2 = await data_api.query_more(result)
    assert result2.done is False
    assert result2.total_size == 10000

    assert result2.records != result.records


@pytest.mark.requires_wiremock
async def test_query_more_with_done_result() -> None:
    data_api = new_data_api()

    result = await data_api.query("SELECT Name FROM Account")
    assert result.done

    result2 = await data_api.query_more(result)
    assert result2.done == result.done
    assert result2.total_size == result.total_size
    assert len(result2.records) == 0


@pytest.mark.requires_wiremock
async def test_query_with_malformed_soql() -> None:
    data_api = new_data_api()

    with pytest.raises(SalesforceRestApiError) as exception_info:
        await data_api.query("SELEKT Name FROM Account")

    assert exception_info.value == SalesforceRestApiError(
        api_errors=[
            InnerSalesforceRestApiError(
                "unexpected token: SELEKT", "MALFORMED_QUERY", []
            )
        ]
    )


@pytest.mark.requires_wiremock
async def test_query_with_unknown_column() -> None:
    data_api = new_data_api()

    with pytest.raises(SalesforceRestApiError) as exception_info:
        await data_api.query("SELECT Bacon__c FROM Account LIMIT 2")

    assert exception_info.value == SalesforceRestApiError(
        api_errors=[
            InnerSalesforceRestApiError(
                "\nSELECT Bacon__c FROM Account LIMIT 2\n       ^\nERROR at Row:1:Column:8\nNo such column 'Bacon__c'"
                " on entity 'Account'. If you are attempting to use a custom field, be sure to append the '__c' after"
                " the custom field name. Please reference your WSDL or the describe call for the appropriate names.",
                "INVALID_FIELD",
                [],
            )
        ]
    )


@pytest.mark.requires_wiremock
async def test_with_sub_query_results() -> None:
    data_api = new_data_api()

    result = await data_api.query(
        "SELECT Account.Name, (SELECT Contact.FirstName, Contact.LastName FROM Account.Contacts) FROM Account LIMIT 5"
    )

    assert result == RecordQueryResult(
        done=True,
        total_size=5,
        records=[
            QueriedRecord(
                type="Account",
                fields={"Name": "GenePoint"},
                sub_query_results={
                    "Contacts": RecordQueryResult(
                        done=True,
                        total_size=1,
                        records=[
                            QueriedRecord(
                                type="Contact",
                                fields={"FirstName": "Edna", "LastName": "Frank"},
                            )
                        ],
                        next_records_url=None,
                    )
                },
            ),
            QueriedRecord(
                type="Account",
                fields={"Name": "United Oil & Gas, UK"},
                sub_query_results={
                    "Contacts": RecordQueryResult(
                        done=True,
                        total_size=1,
                        records=[
                            QueriedRecord(
                                type="Contact",
                                fields={"FirstName": "Ashley", "LastName": "James"},
                            )
                        ],
                        next_records_url=None,
                    )
                },
            ),
            QueriedRecord(
                type="Account",
                fields={"Name": "United Oil & Gas, Singapore"},
                sub_query_results={
                    "Contacts": RecordQueryResult(
                        done=True,
                        total_size=2,
                        records=[
                            QueriedRecord(
                                type="Contact",
                                fields={"FirstName": "Tom", "LastName": "Ripley"},
                            ),
                            QueriedRecord(
                                type="Contact",
                                fields={"FirstName": "Liz", "LastName": "D'Cruz"},
                            ),
                        ],
                        next_records_url=None,
                    )
                },
            ),
            QueriedRecord(
                type="Account",
                fields={"Name": "Edge Communications"},
                sub_query_results={
                    "Contacts": RecordQueryResult(
                        done=True,
                        total_size=2,
                        records=[
                            QueriedRecord(
                                type="Contact",
                                fields={"FirstName": "Rose", "LastName": "Gonzalez"},
                            ),
                            QueriedRecord(
                                type="Contact",
                                fields={"FirstName": "Sean", "LastName": "Forbes"},
                            ),
                        ],
                        next_records_url=None,
                    )
                },
            ),
            QueriedRecord(
                type="Account",
                fields={"Name": "Burlington Textiles Corp of America"},
                sub_query_results={
                    "Contacts": RecordQueryResult(
                        done=True,
                        total_size=1,
                        records=[
                            QueriedRecord(
                                type="Contact",
                                fields={"FirstName": "Jack", "LastName": "Rogers"},
                            )
                        ],
                        next_records_url=None,
                    )
                },
            ),
        ],
        next_records_url=None,
    )


@pytest.mark.requires_wiremock
async def test_query_with_binary_data() -> None:
    data_api = new_data_api()

    result = await data_api.query("SELECT Id, VersionData FROM ContentVersion")

    version_data = result.records[0].fields.get("VersionData")

    assert isinstance(version_data, bytes)
    assert md5(version_data).hexdigest() == "6ea614e1d238a5fee4e7ab39277874fe"


@pytest.mark.requires_wiremock
async def test_create() -> None:
    data_api = new_data_api()

    result = await data_api.create(
        # This example is also used by `tests/fixtures/data_api`.
        # pylint: disable-next=duplicate-code
        Record(
            "Movie__c",
            fields={
                "Name": "Star Wars Episode V: The Empire Strikes Back",
                "Rating__c": "Excellent",
            },
        )
    )

    assert result == "a00B000000FSkcvIAD"


@pytest.mark.requires_wiremock
async def test_create_with_binary_data() -> None:
    data_api = new_data_api()

    result = await data_api.create(
        Record(
            "ContentVersion",
            fields={
                "Title": "File for testing",
                "PathOnClient": "file.bin",
                "VersionData": b"\x04\x08\x15\x16\x23\x42",
            },
        )
    )

    assert result == "0687S00000AX5WVQA1"


@pytest.mark.requires_wiremock
async def test_create_with_binary_data_from_bytearray() -> None:
    data_api = new_data_api()

    result = await data_api.create(
        Record(
            "ContentVersion",
            fields={
                "Title": "File for testing",
                "PathOnClient": "file.bin",
                "VersionData": bytearray(b"\x04\x08\x15\x16\x23\x42"),
            },
        )
    )

    assert result == "0687S00000AX5WVQA1"


@pytest.mark.requires_wiremock
async def test_create_with_invalid_picklist_value() -> None:
    data_api = new_data_api()

    with pytest.raises(SalesforceRestApiError) as exception_info:
        await data_api.create(
            Record(
                "Movie__c",
                fields={
                    "Name": "Star Wars Episode VIII: The Last Jedi",
                    "Rating__c": "Terrible",
                },
            )
        )

    assert exception_info.value == SalesforceRestApiError(
        api_errors=[
            InnerSalesforceRestApiError(
                "Rating: bad value for restricted picklist field: Terrible",
                "INVALID_OR_NULL_FOR_RESTRICTED_PICKLIST",
                ["Rating__c"],
            )
        ]
    )


@pytest.mark.requires_wiremock
async def test_create_with_unknown_object_type() -> None:
    data_api = new_data_api()

    with pytest.raises(SalesforceRestApiError) as exception_info:
        await data_api.create(
            Record(
                "PlayingCard__c",
                fields={
                    "Name": "Ace of Spades",
                },
            )
        )

    assert exception_info.value == SalesforceRestApiError(
        api_errors=[
            InnerSalesforceRestApiError(
                "The requested resource does not exist",
                "NOT_FOUND",
                [],
            )
        ]
    )


@pytest.mark.requires_wiremock
async def test_create_with_invalid_field() -> None:
    data_api = new_data_api()

    with pytest.raises(SalesforceRestApiError) as exception_info:
        await data_api.create(
            Record(
                "Account",
                fields={
                    "FavoritePet__c": "Dog",
                },
            )
        )

    assert exception_info.value == SalesforceRestApiError(
        api_errors=[
            InnerSalesforceRestApiError(
                "No such column 'FavoritePet__c' on sobject of type Account",
                "INVALID_FIELD",
                [],
            )
        ]
    )


@pytest.mark.requires_wiremock
async def test_create_with_required_field_missing() -> None:
    data_api = new_data_api()

    with pytest.raises(SalesforceRestApiError) as exception_info:
        await data_api.create(
            Record(
                "Spaceship__c",
                fields={
                    "Name": "Falcon 9",
                },
            )
        )

    assert exception_info.value == SalesforceRestApiError(
        api_errors=[
            InnerSalesforceRestApiError(
                "Required fields are missing: [Website__c]",
                "REQUIRED_FIELD_MISSING",
                ["Website__c"],
            )
        ]
    )


@pytest.mark.requires_wiremock
async def test_update() -> None:
    data_api = new_data_api()

    result = await data_api.update(
        Record(
            "Movie__c",
            fields={"Id": "a00B000000FSjVUIA1", "ReleaseDate__c": "1980-05-21"},
        )
    )

    assert result == "a00B000000FSjVUIA1"


@pytest.mark.requires_wiremock
async def test_update_with_binary_data() -> None:
    data_api = new_data_api()

    result = await data_api.update(
        Record(
            "ContentVersion",
            fields={
                "Id": "0687S00000AX5kgQAD",
                "VersionData": b"\x04\x08\x15\x16\x23\x42",
            },
        )
    )

    assert result == "0687S00000AX5kgQAD"


@pytest.mark.requires_wiremock
async def test_update_with_binary_data_from_bytearray() -> None:
    data_api = new_data_api()

    result = await data_api.update(
        Record(
            "ContentVersion",
            fields={
                "Id": "0687S00000AX5kgQAD",
                "VersionData": bytearray(b"\x04\x08\x15\x16\x23\x42"),
            },
        )
    )

    assert result == "0687S00000AX5kgQAD"


@pytest.mark.requires_wiremock
async def test_update_without_id_field() -> None:
    data_api = new_data_api()

    with pytest.raises(MissingIdFieldError) as exception_info:
        await data_api.update(
            Record("Movie__c", fields={"ReleaseDate__c": "1980-05-21"})
        )

    assert exception_info.value == MissingIdFieldError()


@pytest.mark.requires_wiremock
async def test_delete() -> None:
    data_api = new_data_api()

    result = await data_api.delete("Account", "001B000001Lp1FxIAJ")

    assert result == "001B000001Lp1FxIAJ"


@pytest.mark.requires_wiremock
async def test_delete_with_already_deleted() -> None:
    data_api = new_data_api()

    with pytest.raises(SalesforceRestApiError) as exception_info:
        await data_api.delete("Account", "001B000001Lp1G2IAJ")

    assert exception_info.value == SalesforceRestApiError(
        [InnerSalesforceRestApiError("entity is deleted", "ENTITY_IS_DELETED", [])]
    )


@pytest.mark.requires_wiremock
async def test_access_token() -> None:
    data_api = new_data_api()

    assert data_api.access_token == "EXAMPLE-TOKEN"


@pytest.mark.requires_wiremock
async def test_unit_of_work() -> None:
    data_api = new_data_api()
    unit_of_work = UnitOfWork()

    franchise_reference_id = unit_of_work.register_create(
        Record("Franchise__c", {"Name": "Star Wars"})
    )

    unit_of_work.register_create(
        Record(
            "Movie__c",
            {
                "Name": "Star Wars Episode I - A Phantom Menace",
                "Franchise__c": franchise_reference_id,
            },
        )
    )

    unit_of_work.register_create(
        Record(
            "Movie__c",
            {
                "Name": "Star Wars Episode II - Attack Of The Clones",
                "Franchise__c": franchise_reference_id,
            },
        )
    )

    unit_of_work.register_create(
        Record(
            "Movie__c",
            {
                "Name": "Star Wars Episode III - Revenge Of The Sith",
                "Franchise__c": franchise_reference_id,
            },
        )
    )

    result = await data_api.commit_unit_of_work(unit_of_work)

    assert result == {
        ReferenceId("referenceId0"): "a03B0000007BhQQIA0",
        ReferenceId("referenceId1"): "a00B000000FSkioIAD",
        ReferenceId("referenceId2"): "a00B000000FSkipIAD",
        ReferenceId("referenceId3"): "a00B000000FSkiqIAD",
    }


@pytest.mark.requires_wiremock
async def test_unit_of_work_update() -> None:
    data_api = new_data_api()
    unit_of_work = UnitOfWork()

    update_record_reference = unit_of_work.register_update(
        Record(
            "Movie__c",
            fields={"Id": "a01B0000009gSrFIAU", "ReleaseDate__c": "1980-05-21"},
        )
    )

    result = await data_api.commit_unit_of_work(unit_of_work)

    assert result == {update_record_reference: "a01B0000009gSrFIAU"}


@pytest.mark.requires_wiremock
async def test_unit_of_work_delete() -> None:
    data_api = new_data_api()
    unit_of_work = UnitOfWork()

    delete_record_reference = unit_of_work.register_delete(
        "Movie__c", "a01B0000009gSr9IAE"
    )

    result = await data_api.commit_unit_of_work(unit_of_work)

    assert result == {delete_record_reference: "a01B0000009gSr9IAE"}


@pytest.mark.requires_wiremock
async def test_unit_of_work_single_create() -> None:
    data_api = new_data_api()
    unit_of_work = UnitOfWork()

    unit_of_work.register_create(
        Record(
            type="Movie__c",
            fields={
                "Name": "Star Wars Episode IV - A New Hope",
                "Rating__c": "Excellent",
            },
        )
    )

    result = await data_api.commit_unit_of_work(unit_of_work)

    assert result == {
        ReferenceId("referenceId0"): "a01B0000009gSoxIAE",
    }


@pytest.mark.requires_wiremock
async def test_unit_of_work_single_create_with_error() -> None:
    data_api = new_data_api()
    unit_of_work = UnitOfWork()

    unit_of_work.register_create(
        Record(
            type="Movie__c",
            fields={
                "Name": "Star Wars Episode IV - A New Hope",
                "Rating__c": "Amazing",
            },
        )
    )

    with pytest.raises(SalesforceRestApiError) as exception_info:
        await data_api.commit_unit_of_work(unit_of_work)

    assert exception_info.value == SalesforceRestApiError(
        api_errors=[
            InnerSalesforceRestApiError(
                "Rating: bad value for restricted picklist field: Amazing",
                "INVALID_OR_NULL_FOR_RESTRICTED_PICKLIST",
                ["Rating__c"],
            )
        ]
    )


@pytest.mark.requires_wiremock
async def test_unit_of_work_single_update() -> None:
    data_api = new_data_api()
    unit_of_work = UnitOfWork()

    unit_of_work.register_update(
        Record(
            type="Movie__c",
            fields={"Id": "a01B0000009gSrFIAU", "ReleaseDate__c": "1980-05-21"},
        )
    )

    result = await data_api.commit_unit_of_work(unit_of_work)

    assert result == {
        ReferenceId("referenceId0"): "a01B0000009gSrFIAU",
    }


@pytest.mark.requires_wiremock
async def test_unit_of_work_single_delete() -> None:
    data_api = new_data_api()
    unit_of_work = UnitOfWork()

    unit_of_work.register_delete("Movie__c", "a01B0000009gSr9IAE")

    result = await data_api.commit_unit_of_work(unit_of_work)

    assert result == {
        ReferenceId("referenceId0"): "a01B0000009gSr9IAE",
    }


@pytest.mark.requires_wiremock
async def test_query_with_associated_record_results() -> None:
    data_api = new_data_api()

    result = await data_api.query("SELECT Name, Owner.Name from Account LIMIT 1")

    assert result == RecordQueryResult(
        done=True,
        total_size=1,
        next_records_url=None,
        records=[
            QueriedRecord(
                type="Account",
                fields={
                    "Name": "TestAccount5",
                    "Owner": QueriedRecord(type="User", fields={"Name": "Guy Smiley"}),
                },
            )
        ],
    )


@pytest.mark.requires_wiremock
async def test_session() -> None:
    """
    Tests use of a shared client session (as is used when DataAPI is initialised in the ASGI app).

    Ensures that the session remains valid for multiple requests, ie: that it's been left open
    after each request (including when requests fail). The query used is one that returns binary
    data, to ensure that the session handling in `DataAPI._download_file()` is exercised too.
    """
    async with (
        DataAPI._create_session()  # pyright: ignore [reportPrivateUsage] pylint:disable=protected-access
    ) as session:
        data_api = new_data_api(session=session)

        first_result = await data_api.query(
            "SELECT Id, VersionData FROM ContentVersion"
        )
        assert first_result.total_size == 1

        with pytest.raises(UnexpectedRestApiResponsePayload):
            await data_api.query("SELECT Name FROM FruitVendor__c")

        second_result = await data_api.query(
            "SELECT Id, VersionData FROM ContentVersion"
        )
        assert second_result.total_size == 1
