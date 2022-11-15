from salesforce_functions import Context, InvocationEvent  # isort:skip

# An absolute path import for a package in the function's root directory.
# pylint: disable-next=import-error,wrong-import-order
from example_module import example_function


async def function(_event: InvocationEvent[None], _context: Context):
    example_function()
    return None
