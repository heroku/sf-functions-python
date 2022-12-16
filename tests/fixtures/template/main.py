from typing import Any

from salesforce_functions import Context, InvocationEvent, get_logger

# The type of the data payload sent with the invocation event.
# Change this to a more specific type matching the expected payload for
# improved IDE auto-completion and linting coverage. For example:
# `EventPayloadType = dict[str, Any]`
EventPayloadType = Any

logger = get_logger()


# These mypy/pylint annotations do not exist in the upstream template. They are required here since
# we have strict linting/type-checking enabled for this repository, that would otherwise require
# `context` to be marked as unused (eg: `_context`) and for an explicit return type to be specified
# (which could harm the UX of using the template, for those less comfortable with Python types).
# mypy: disable-error-code=no-untyped-def
# pylint: disable-next=unused-argument
async def function(event: InvocationEvent[EventPayloadType], context: Context):
    """Describe the function here."""

    result = await context.org.data_api.query("SELECT Id, Name FROM Account")
    logger.info(f"Function successfully queried {result.total_size} account records!")

    return result.records
