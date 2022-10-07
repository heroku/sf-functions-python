from salesforce_functions import Context, InvocationEvent, get_logger

EventPayloadType = dict[str, str]
logger = get_logger()


async def function(event: InvocationEvent[EventPayloadType], context: Context):
    logger.info("Hello!")
    # if context.org is not None:
    #     result = await context.org.data_api.query("SELECT Name FROM User")
    #     logger.info(f"Result: {result}")
    return {"foo": "bar"}
