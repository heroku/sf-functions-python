from salesforce_functions import Context, InvocationEvent

# An import that's relative to the function's root directory.
from .example_module import example_function


async def function(event: InvocationEvent[None], context: Context):
    example_function()
    return None
