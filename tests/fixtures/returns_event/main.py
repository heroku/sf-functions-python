from typing import Any

from salesforce_functions import Context, InvocationEvent


async def function(event: InvocationEvent[Any], _context: Context):
    return event
