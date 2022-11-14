from salesforce_functions import Context, InvocationEvent


async def function(event: InvocationEvent[None], context: Context):
    return set("Sets cannot be serialized")
