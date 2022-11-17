from salesforce_functions import Context, InvocationEvent


async def function(_event: InvocationEvent[None], _context: Context) -> set[str]:
    return set("Sets cannot be serialized")
