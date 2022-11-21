from typing import Any

from salesforce_functions import Context, InvocationEvent


async def function(_event: InvocationEvent[Any], _context: Context) -> None:
    return None
