from salesforce_functions import Context, InvocationEvent


async def wrong_function_name(event: InvocationEvent[None], context: Context):
    return None
