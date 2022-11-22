from typing import Any

from salesforce_functions import Context, InvocationEvent, Record


async def function(_event: InvocationEvent[Any], context: Context) -> str:
    assert context.org is not None
    record_id = await context.org.data_api.create(
        Record(
            "Movie__c",
            fields={
                "Name": "Star Wars Episode V: The Empire Strikes Back",
                "Rating__c": "Excellent",
            },
        )
    )
    return record_id
