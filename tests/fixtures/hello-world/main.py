# import logging

from salesforce_functions import Context, InvocationEvent

EventPayloadType = dict[str, str]
# logger = logging.getLogger(__name__)


async def function(event: InvocationEvent[EventPayloadType], context: Context):
    # logging.warning(__name__)
    # if context.org is not None:
    #     result = await context.org.data_api.query("SELECT Name FROM User")
    #     print(f"Result: {result}")
    return {"foo": "bar"}
