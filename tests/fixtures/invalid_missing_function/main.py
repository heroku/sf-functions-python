from salesforce_functions import Context, InvocationEvent


async def wrong_function_name(_event: InvocationEvent[None], _context: Context):
    return None
