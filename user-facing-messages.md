# Python Functions user-facing messages

## CLI help text

Note: End users mostly won't use the sf-functions-python CLI directly, since they will
instead use the sf CLI which wraps it - however, I'm including these for completeness.

### sf-functions-python --help

```term
usage: sf-functions-python [-h] {check,serve,version} ...

Salesforce Functions Python Runtime

options:
  -h, --help            show this help message and exit

subcommands:
  {check,serve,version}
    check               Checks that a function project is configured correctly
    serve               Serves a function project via HTTP
    version             Prints the version of the Python Functions Runtime
```

### sf-functions-python check --help

```term
usage: sf-functions-python check [-h] <project-path>

positional arguments:
  <project-path>  The directory that contains the function

options:
  -h, --help      show this help message and exit
```

### sf-functions-python serve --help

```term
usage: sf-functions-python serve [-h] [--host HOST] [-p PORT] [-w WORKERS]
                                 <project-path>

positional arguments:
  <project-path>        The directory that contains the function

options:
  -h, --help            show this help message and exit
  --host HOST           The host on which the web server binds (default:
                        localhost)
  -p PORT, --port PORT  The port on which the web server listens (default:
                        8080)
  -w WORKERS, --workers WORKERS
                        The number of worker processes (default: 1)
```

## Checking/running a valid function

In the context of the buildpack self-check:

```term
Function passed validation.
```

In the context of the CLI start command:

```term
Starting sf-functions-python v0.4.0 in single process mode.
INFO:     Started server process [81699]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://localhost:8080 (Press CTRL+C to quit)
```

## Checking/running functions that fail the self-check

Note: The same base error message is used for both the self-check and the start command, however,
the prefix is different ('Function failed validation:' vs 'Unable to load function: ' etc).

### tests/fixtures/invalid_missing_function

In the context of the production deploy self-check:

```term
Function failed validation: Didn't find a function named 'function' in main.py.
```

In the context of the CLI start command:

```term
Starting sf-functions-python v0.4.0 in single process mode.
INFO:     Started server process [81710]
INFO:     Waiting for application startup.
ERROR:    RuntimeError: Unable to load function: Didn't find a function named 'function' in main.py.

ERROR:    Application startup failed. Exiting.
```

### tests/fixtures/invalid_missing_main_py

In the context of the production deploy self-check:

```term
Function failed validation: Didn't find a main.py file at /Users/emorley/src/sf-functions-python/tests/fixtures/invalid_missing_main_py/main.py.
```

In the context of the CLI start command:

```term
Starting sf-functions-python v0.4.0 in single process mode.
INFO:     Started server process [81712]
INFO:     Waiting for application startup.
ERROR:    RuntimeError: Unable to load function: Didn't find a main.py file at /Users/emorley/src/sf-functions-python/tests/fixtures/invalid_missing_main_py/main.py.

ERROR:    Application startup failed. Exiting.
```

### tests/fixtures/invalid_not_a_function

In the context of the production deploy self-check:

```term
Function failed validation: Didn't find a function named 'function' in main.py.
```

In the context of the CLI start command:

```term
Starting sf-functions-python v0.4.0 in single process mode.
INFO:     Started server process [81714]
INFO:     Waiting for application startup.
ERROR:    RuntimeError: Unable to load function: Didn't find a function named 'function' in main.py.

ERROR:    Application startup failed. Exiting.
```

### tests/fixtures/invalid_not_async

In the context of the production deploy self-check:

```term
Function failed validation: The function named 'function' in main.py must be an async function. Change the function definition from 'def function' to 'async def function'.
```

In the context of the CLI start command:

```term
Starting sf-functions-python v0.4.0 in single process mode.
INFO:     Started server process [81716]
INFO:     Waiting for application startup.
ERROR:    RuntimeError: Unable to load function: The function named 'function' in main.py must be an async function. Change the function definition from 'def function' to 'async def function'.

ERROR:    Application startup failed. Exiting.
```

### tests/fixtures/invalid_number_of_args

In the context of the production deploy self-check:

```term
Function failed validation: The function named 'function' in main.py has the wrong number of parameters (expected 2 but found 3).
```

In the context of the CLI start command:

```term
Starting sf-functions-python v0.4.0 in single process mode.
INFO:     Started server process [81718]
INFO:     Waiting for application startup.
ERROR:    RuntimeError: Unable to load function: The function named 'function' in main.py has the wrong number of parameters (expected 2 but found 3).

ERROR:    Application startup failed. Exiting.
```

### tests/fixtures/invalid_syntax_error

In the context of the production deploy self-check:

```term
Function failed validation: Couldn't import main.py:

Traceback (most recent call last):
  File "/Users/emorley/src/sf-functions-python/salesforce_functions/_internal/function_loader.py", line 57, in load_function
    spec.loader.exec_module(module)
  File "<frozen importlib._bootstrap_external>", line 936, in exec_module
  File "<frozen importlib._bootstrap_external>", line 1074, in get_code
  File "<frozen importlib._bootstrap_external>", line 1004, in source_to_code
  File "<frozen importlib._bootstrap>", line 241, in _call_with_frames_removed
  File "/Users/emorley/src/sf-functions-python/tests/fixtures/invalid_syntax_error/main.py", line 2
    syntax error!
           ^^^^^
SyntaxError: invalid syntax

```

In the context of the CLI start command:

```term
Starting sf-functions-python v0.4.0 in single process mode.
INFO:     Started server process [81722]
INFO:     Waiting for application startup.
ERROR:    RuntimeError: Unable to load function: Couldn't import main.py:

Traceback (most recent call last):
  File "/Users/emorley/src/sf-functions-python/salesforce_functions/_internal/function_loader.py", line 57, in load_function
    spec.loader.exec_module(module)
  File "<frozen importlib._bootstrap_external>", line 936, in exec_module
  File "<frozen importlib._bootstrap_external>", line 1074, in get_code
  File "<frozen importlib._bootstrap_external>", line 1004, in source_to_code
  File "<frozen importlib._bootstrap>", line 241, in _call_with_frames_removed
  File "/Users/emorley/src/sf-functions-python/tests/fixtures/invalid_syntax_error/main.py", line 2
    syntax error!
           ^^^^^
SyntaxError: invalid syntax


ERROR:    Application startup failed. Exiting.
```

### tests/fixtures/project_toml_api_version_invalid

In the context of the production deploy self-check:

```term
Function failed validation: '55' isn't a valid Salesforce REST API version. Update the 'salesforce-api-version' key in project.toml to a version that uses the form 'X.Y', such as '56.0'.
```

In the context of the CLI start command:

```term
Starting sf-functions-python v0.4.0 in single process mode.
INFO:     Started server process [81724]
INFO:     Waiting for application startup.
ERROR:    RuntimeError: Unable to load function: '55' isn't a valid Salesforce REST API version. Update the 'salesforce-api-version' key in project.toml to a version that uses the form 'X.Y', such as '56.0'.

ERROR:    Application startup failed. Exiting.
```

### tests/fixtures/project_toml_api_version_missing

In the context of the production deploy self-check:

```term
Function failed validation: The project.toml file is missing the required 'com.salesforce.salesforce-api-version' key.
```

In the context of the CLI start command:

```term
Starting sf-functions-python v0.4.0 in single process mode.
INFO:     Started server process [81726]
INFO:     Waiting for application startup.
ERROR:    RuntimeError: Unable to load function: The project.toml file is missing the required 'com.salesforce.salesforce-api-version' key.

ERROR:    Application startup failed. Exiting.
```

### tests/fixtures/project_toml_api_version_too_old

In the context of the production deploy self-check:

```term
Function failed validation: Salesforce REST API version '52.1' isn't supported. Update the 'salesforce-api-version' key in project.toml to '53.0' or later.
```

In the context of the CLI start command:

```term
Starting sf-functions-python v0.4.0 in single process mode.
INFO:     Started server process [81728]
INFO:     Waiting for application startup.
ERROR:    RuntimeError: Unable to load function: Salesforce REST API version '52.1' isn't supported. Update the 'salesforce-api-version' key in project.toml to '53.0' or later.

ERROR:    Application startup failed. Exiting.
```

### tests/fixtures/project_toml_api_version_wrong_type

In the context of the production deploy self-check:

```term
Function failed validation: The 'com.salesforce.salesforce-api-version' key in project.toml must be a string.
```

In the context of the CLI start command:

```term
Starting sf-functions-python v0.4.0 in single process mode.
INFO:     Started server process [81732]
INFO:     Waiting for application startup.
ERROR:    RuntimeError: Unable to load function: The 'com.salesforce.salesforce-api-version' key in project.toml must be a string.

ERROR:    Application startup failed. Exiting.
```

### tests/fixtures/project_toml_file_missing

In the context of the production deploy self-check:

```term
Function failed validation: Didn't find a project.toml file at /Users/emorley/src/sf-functions-python/tests/fixtures/project_toml_file_missing/project.toml.
```

In the context of the CLI start command:

```term
Starting sf-functions-python v0.4.0 in single process mode.
INFO:     Started server process [81734]
INFO:     Waiting for application startup.
ERROR:    RuntimeError: Unable to load function: Didn't find a project.toml file at /Users/emorley/src/sf-functions-python/tests/fixtures/project_toml_file_missing/project.toml.

ERROR:    Application startup failed. Exiting.
```

### tests/fixtures/project_toml_invalid_toml

In the context of the production deploy self-check:

```term
Function failed validation: The project.toml file isn't valid TOML: Expected '=' after a key in a key/value pair (at line 1, column 4)
```

In the context of the CLI start command:

```term
Starting sf-functions-python v0.4.0 in single process mode.
INFO:     Started server process [81736]
INFO:     Waiting for application startup.
ERROR:    RuntimeError: Unable to load function: The project.toml file isn't valid TOML: Expected '=' after a key in a key/value pair (at line 1, column 4)

ERROR:    Application startup failed. Exiting.
```

### tests/fixtures/project_toml_invalid_unicode

In the context of the production deploy self-check:

```term
Function failed validation: Couldn't read project.toml: UnicodeDecodeError: 'utf-8' codec can't decode byte 0x80 in position 0: invalid start byte
```

In the context of the CLI start command:

```term
Starting sf-functions-python v0.4.0 in single process mode.
INFO:     Started server process [81738]
INFO:     Waiting for application startup.
ERROR:    RuntimeError: Unable to load function: Couldn't read project.toml: UnicodeDecodeError: 'utf-8' codec can't decode byte 0x80 in position 0: invalid start byte

ERROR:    Application startup failed. Exiting.
```

### tests/fixtures/project_toml_salesforce_table_missing

In the context of the production deploy self-check:

```term
Function failed validation: The project.toml file is missing the required '[com.salesforce]' table.
```

In the context of the CLI start command:

```term
Starting sf-functions-python v0.4.0 in single process mode.
INFO:     Started server process [81740]
INFO:     Waiting for application startup.
ERROR:    RuntimeError: Unable to load function: The project.toml file is missing the required '[com.salesforce]' table.

ERROR:    Application startup failed. Exiting.
```

### tests/fixtures/project_toml_salesforce_table_wrong_type

In the context of the production deploy self-check:

```term
Function failed validation: The project.toml file is missing the required '[com.salesforce]' table.
```

In the context of the CLI start command:

```term
Starting sf-functions-python v0.4.0 in single process mode.
INFO:     Started server process [81742]
INFO:     Waiting for application startup.
ERROR:    RuntimeError: Unable to load function: The project.toml file is missing the required '[com.salesforce]' table.

ERROR:    Application startup failed. Exiting.
```

## Functions that fail at runtime

These are cases we cannot catch using the self-check, as they only occur when the function is running.

### tests/fixtures/raises_exception_at_runtime

Server log:

```term
Starting sf-functions-python v0.4.0 in single process mode.
INFO:     Started server process [81743]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://localhost:8080 (Press CTRL+C to quit)
Traceback (most recent call last):
  File "/Users/emorley/src/sf-functions-python/salesforce_functions/_internal/app.py", line 79, in _handle_function_invocation
    function_result = await function(event, context)
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/emorley/src/sf-functions-python/tests/fixtures/raises_exception_at_runtime/main.py", line 5, in function
    return 1 / 0
           ~~^~~
ZeroDivisionError: division by zero
invocationId=00DJS0000000123ABC-11ae4dba887048af5afc4027b85b076d level=error msg="Exception occurred while executing function: ZeroDivisionError: division by zero"
```

### tests/fixtures/return_value_not_serializable

Server log:

```term
Starting sf-functions-python v0.4.0 in single process mode.
INFO:     Started server process [81754]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://localhost:8080 (Press CTRL+C to quit)
invocationId=00DJS0000000123ABC-41e01168ebecb8164c20369465fa6769 level=error msg="Function return value can't be serialized: TypeError: Type is not JSON serializable: set"
```

### Invalid CloudEvent payload (should not be possible to trigger this in practice)

Server log:

```term
Starting sf-functions-python v0.4.0 in single process mode.
INFO:     Started server process [81767]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://localhost:8080 (Press CTRL+C to quit)
level=error msg="Couldn't parse CloudEvent: Data payload isn't valid JSON: invalid literal: line 1 column 1 (char 0)"
```
