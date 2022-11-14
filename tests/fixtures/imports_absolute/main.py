from salesforce_functions import Context, InvocationEvent

# An absolute path import for a package in the function's root directory.
from example_module import example_function


async def function(event: InvocationEvent[None], context: Context):
    example_function()
    return None
