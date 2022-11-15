from salesforce_functions import Context, InvocationEvent, get_logger

EventPayloadType = int
logger = get_logger()


async def function(_event: InvocationEvent[EventPayloadType], _context: Context):
    print("Print works but output isn't structured")

    # The debug message won't be under the default log level of INFO.
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")

    logger.info("Info message with custom metadata", record_id=12345)
