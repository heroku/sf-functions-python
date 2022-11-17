from salesforce_functions import Context, InvocationEvent

# An import that's relative to the function's root directory.
# pylint: disable-next=import-error
from .example_module import example_function


async def function(_event: InvocationEvent[None], _context: Context) -> None:
    example_function()
    return None
