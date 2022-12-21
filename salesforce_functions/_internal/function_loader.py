import importlib.util
import inspect
import sys
import traceback
import typing
from pathlib import Path
from typing import Any, Awaitable, Callable

from ..context import Context
from ..invocation_event import InvocationEvent

FUNCTION_MODULE_NAME = "main"
FUNCTION_NAME = "function"

Function = Callable[[InvocationEvent[Any], Context], Awaitable[Any]]


def load_function(project_path: Path) -> Function:
    """
    Load and validate the function inside `main.py` in the specified directory.

    Uses the approach documented here:
    https://docs.python.org/3/library/importlib.html#importing-a-source-file-directly
    """
    # Convert `project_path` to a normalised absolute path, so that:
    # - it's clearer in any error messages where we were attempting to look for the function
    # - we don't end up putting a relative path onto `sys.path`.
    project_path = project_path.resolve()
    module_filename = f"{FUNCTION_MODULE_NAME}.py"
    module_path = project_path.joinpath(module_filename)

    if not module_path.is_file():
        raise LoadFunctionError(
            f"A {module_filename} file was not found at: {module_path}"
        )

    # `submodule_search_locations` is set to ensure relative imports work within the imported module.
    spec = importlib.util.spec_from_file_location(
        FUNCTION_MODULE_NAME,
        module_path,
        submodule_search_locations=[str(project_path)],
    )

    # These can only be None if our implementation is incorrect (eg: trying to load a file that
    # doesn't have a .py extension, so has no known loader). The assertions are to prove this
    # to the type checker.
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    sys.modules[FUNCTION_MODULE_NAME] = module

    # Allow the imported module to use absolute imports for modules within it's own directory.
    sys.path.insert(0, str(project_path))

    try:
        spec.loader.exec_module(module)
    except Exception as e:  # e.g.: SyntaxError, ImportError, NameError.
        raise LoadFunctionError(
            f"Could not import {module_filename}:\n\n{traceback.format_exc()}"
        ) from e

    function = getattr(module, FUNCTION_NAME, None)

    if function is None or not inspect.isfunction(function):
        raise LoadFunctionError(
            f"A function named '{FUNCTION_NAME}' was not found in {module_filename}."
        )

    if not inspect.iscoroutinefunction(function):
        raise LoadFunctionError(
            f"The function named '{FUNCTION_NAME}' in {module_filename} must be an async function."
            f" Change the function definition from 'def {FUNCTION_NAME}' to 'async def {FUNCTION_NAME}'."
        )

    parameter_count = len(inspect.signature(function).parameters)
    expected_parameter_count = len(typing.get_args(Function)[0])

    if parameter_count != expected_parameter_count:
        raise LoadFunctionError(
            f"The function named '{FUNCTION_NAME}' in {module_filename} has the wrong number of"
            f" parameters (expected {expected_parameter_count} but found {parameter_count})."
        )

    return function


class LoadFunctionError(Exception):
    """There was an error loading the function or it failed validation."""
