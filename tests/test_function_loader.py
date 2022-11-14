import inspect
from pathlib import Path

import pytest

from salesforce_functions._internal.function_loader import (
    load_function,
    LoadFunctionError,
)


def test_basic_function():
    fixture = Path("tests/fixtures/basic")
    function = load_function(fixture)
    assert inspect.iscoroutinefunction(function)
    assert function.__module__ == "main"
    assert function.__name__ == "function"


def test_function_with_relative_imports():
    """Test using imports that are relative to the function's root directory."""
    fixture = Path("tests/fixtures/imports_relative")
    load_function(fixture)


def test_function_with_absolute_imports():
    """Test using absolute path imports for packages in the function's root directory."""
    fixture = Path("tests/fixtures/imports_absolute")
    load_function(fixture)


def test_function_without_type_annotations():
    fixture = Path("tests/fixtures/without_type_annotations")
    load_function(fixture)


def test_invalid_function_nonexistent_directory():
    fixture = Path("this_directory_does_not_exist")
    absolute_fixture_path = fixture.resolve()
    expected_message = rf"File not found: {absolute_fixture_path}/main\.py$"

    with pytest.raises(LoadFunctionError, match=expected_message):
        load_function(fixture)


def test_invalid_function_missing_module():
    fixture = Path("tests/fixtures/invalid_missing_main_py")
    absolute_fixture_path = fixture.resolve()
    expected_message = rf"File not found: {absolute_fixture_path}/main\.py$"

    with pytest.raises(LoadFunctionError, match=expected_message):
        load_function(fixture)


def test_invalid_function_syntax_error():
    fixture = Path("tests/fixtures/invalid_syntax_error")
    expected_message = r"""Exception during import:

Traceback \(most recent call last\):
(?s:.+)
SyntaxError: invalid syntax
$"""

    with pytest.raises(LoadFunctionError, match=expected_message):
        load_function(fixture)


def test_invalid_function_missing_function():
    fixture = Path("tests/fixtures/invalid_missing_function")
    absolute_fixture_path = fixture.resolve()
    expected_message = rf"A function named 'function' was not found in: {absolute_fixture_path}/main\.py$"

    with pytest.raises(LoadFunctionError, match=expected_message):
        load_function(fixture)


def test_invalid_function_not_a_function():
    fixture = Path("tests/fixtures/invalid_not_a_function")
    absolute_fixture_path = fixture.resolve()
    expected_message = rf"A function named 'function' was not found in: {absolute_fixture_path}/main\.py$"

    with pytest.raises(LoadFunctionError, match=expected_message):
        load_function(fixture)


def test_invalid_function_not_async():
    fixture = Path("tests/fixtures/invalid_not_async")
    expected_message = rf"The function named 'function' must be an async function\. Change the function definition from 'def function' to 'async def function'\.$"

    with pytest.raises(LoadFunctionError, match=expected_message):
        load_function(fixture)


def test_invalid_function_number_of_args():
    fixture = Path("tests/fixtures/invalid_number_of_args")
    expected_message = rf"The function named 'function' has the wrong number of parameters \(expected 2 but found 3\)\.$"

    with pytest.raises(LoadFunctionError, match=expected_message):
        load_function(fixture)
