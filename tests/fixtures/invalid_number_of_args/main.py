from typing import Any

from salesforce_functions import Context, InvocationEvent


async def function(
    event: InvocationEvent[Any], context: Context, unexpected_argument: Any
):
    return None
