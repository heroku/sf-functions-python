from salesforce_functions import Context, InvocationEvent


async def function(event: InvocationEvent[None], context: Context) -> float:
    return 1 / 0
