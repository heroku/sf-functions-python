import importlib.util
import sys
from pathlib import Path
from typing import Any, Awaitable, Callable

from .exceptions import SalesforceFunctionError
from ..context import Context
from ..invocation_event import InvocationEvent

UserFunction = Callable[[InvocationEvent[Any], Context], Awaitable[Any]]


# Load the user function using the approach documented here:
# https://docs.python.org/3/library/importlib.html#importing-a-source-file-directly
def load_user_function(project_path: Path) -> UserFunction:
    # Convert `project_path` to a normalised absolute path, so that:
    # - it's clearer in any error messages where we were attempting to look for the function
    # - we don't end up putting a relative path onto `sys.path`.
    project_path = project_path.resolve()

    # TODO: Should these be user configurable? If so, how? What should the default values be?
    module_name = "main"
    function_name = "function"
    module_path = project_path.joinpath(f"{module_name}.py")

    if not module_path.exists():
        # TODO: Decide how to structure exception types.
        # TODO: Include explanation of where the module name came from?
        raise SalesforceFunctionError(f"Function file not found: {module_path}")

    # `submodule_search_locations` is set to ensure relative imports work from the function.
    spec = importlib.util.spec_from_file_location(
        module_name, module_path, submodule_search_locations=[str(project_path)]
    )

    # TODO: Figure out when this can even occur and adjust message accordingly
    # (without it the type checker is not happy)
    if spec is None or spec.loader is None:
        raise SalesforceFunctionError("Unknown error whilst loading function")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module

    # Allow the function to use absolute imports for modules within the package's directory.
    sys.path.insert(0, str(project_path))

    try:
        spec.loader.exec_module(module)
    except Exception as e:
        # TODO: Fix this since it loses the useful part of SyntaxErrors etc
        raise SalesforceFunctionError(f"Error importing function: {e}")

    try:
        function = getattr(module, function_name)
    except AttributeError:
        # TODO: Clean this up
        raise SalesforceFunctionError(
            f"Function with name '{function_name}' does not exist in '{module_path}'!"
        )

    # TODO: Check shape of function is correct, eg:
    # https://github.com/GoogleCloudPlatform/functions-framework-python/blob/master/src/functions_framework/_function_registry.py#L37-L60
    return function
