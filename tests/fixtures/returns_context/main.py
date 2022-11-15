import dataclasses
from typing import Any

from salesforce_functions import Context, InvocationEvent


async def function(_event: InvocationEvent[Any], context: Context):
    # `context.org.data_api` is an instance of `DataAPI` which is not JSON serializable,
    # so it has to be replaced so that the function return value can be serialized.
    org_without_data_api = dataclasses.replace(context.org, data_api=None)
    return dataclasses.replace(context, org=org_without_data_api)
