from salesforce_functions import Context, InvocationEvent


async def function(_event: InvocationEvent[None], _context: Context) -> float:
    return 1 / 0
