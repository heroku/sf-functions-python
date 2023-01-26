# Python Functions user-facing success/error messages

## Valid/working function

In the context of the buildpack self-check:

```term
Function passed validation
```

In the context of the CLI start command:

```term
Starting sf-functions-python v0.4.0 in single process mode.
INFO:     Started server process [81699]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://localhost:8080 (Press CTRL+C to quit)
```

## Functions that fail the self-check

Note: The same base error message is used for both the self-check and the start command, however,
the prefix is different ('Function failed validation:' vs 'Unable to load function: ' etc).

### tests/fixtures/invalid_missing_function

In the context of the production deploy self-check:

```term
Function failed validation: A project.toml file was not found at: /Users/emorley/src/sf-functions-python/tests/fixtures/invalid_missing_function/project.toml
```

In the context of the CLI start command:

```term
Starting sf-functions-python v0.4.0 in single process mode.
INFO:     Started server process [81710]
INFO:     Waiting for application startup.
ERROR:    RuntimeError: Unable to load function: A project.toml file was not found at: /Users/emorley/src/sf-functions-python/tests/fixtures/invalid_missing_function/project.toml

ERROR:    Application startup failed. Exiting.
```

### tests/fixtures/invalid_missing_main_py

In the context of the production deploy self-check:

```term
Function failed validation: A main.py file was not found at: /Users/emorley/src/sf-functions-python/tests/fixtures/invalid_missing_main_py/main.py
```

In the context of the CLI start command:

```term
Starting sf-functions-python v0.4.0 in single process mode.
INFO:     Started server process [81712]
INFO:     Waiting for application startup.
ERROR:    RuntimeError: Unable to load function: A main.py file was not found at: /Users/emorley/src/sf-functions-python/tests/fixtures/invalid_missing_main_py/main.py

ERROR:    Application startup failed. Exiting.
```

### tests/fixtures/invalid_not_a_function

In the context of the production deploy self-check:

```term
Function failed validation: A project.toml file was not found at: /Users/emorley/src/sf-functions-python/tests/fixtures/invalid_not_a_function/project.toml
```

In the context of the CLI start command:

```term
Starting sf-functions-python v0.4.0 in single process mode.
INFO:     Started server process [81714]
INFO:     Waiting for application startup.
ERROR:    RuntimeError: Unable to load function: A project.toml file was not found at: /Users/emorley/src/sf-functions-python/tests/fixtures/invalid_not_a_function/project.toml

ERROR:    Application startup failed. Exiting.
```

### tests/fixtures/invalid_not_async

In the context of the production deploy self-check:

```term
Function failed validation: A project.toml file was not found at: /Users/emorley/src/sf-functions-python/tests/fixtures/invalid_not_async/project.toml
```

In the context of the CLI start command:

```term
Starting sf-functions-python v0.4.0 in single process mode.
INFO:     Started server process [81716]
INFO:     Waiting for application startup.
ERROR:    RuntimeError: Unable to load function: A project.toml file was not found at: /Users/emorley/src/sf-functions-python/tests/fixtures/invalid_not_async/project.toml

ERROR:    Application startup failed. Exiting.
```

### tests/fixtures/invalid_number_of_args

In the context of the production deploy self-check:

```term
Function failed validation: A project.toml file was not found at: /Users/emorley/src/sf-functions-python/tests/fixtures/invalid_number_of_args/project.toml
```

In the context of the CLI start command:

```term
Starting sf-functions-python v0.4.0 in single process mode.
INFO:     Started server process [81718]
INFO:     Waiting for application startup.
ERROR:    RuntimeError: Unable to load function: A project.toml file was not found at: /Users/emorley/src/sf-functions-python/tests/fixtures/invalid_number_of_args/project.toml

ERROR:    Application startup failed. Exiting.
```

### tests/fixtures/invalid_syntax_error

In the context of the production deploy self-check:

```term
Function failed validation: A project.toml file was not found at: /Users/emorley/src/sf-functions-python/tests/fixtures/invalid_syntax_error/project.toml
```

In the context of the CLI start command:

```term
Starting sf-functions-python v0.4.0 in single process mode.
INFO:     Started server process [81722]
INFO:     Waiting for application startup.
ERROR:    RuntimeError: Unable to load function: A project.toml file was not found at: /Users/emorley/src/sf-functions-python/tests/fixtures/invalid_syntax_error/project.toml

ERROR:    Application startup failed. Exiting.
```

### tests/fixtures/project_toml_api_version_invalid

In the context of the production deploy self-check:

```term
Function failed validation: '55' is not a valid Salesforce REST API version. Update 'salesforce-api-version' in project.toml to a version of form 'X.Y'.
```

In the context of the CLI start command:

```term
Starting sf-functions-python v0.4.0 in single process mode.
INFO:     Started server process [81724]
INFO:     Waiting for application startup.
ERROR:    RuntimeError: Unable to load function: '55' is not a valid Salesforce REST API version. Update 'salesforce-api-version' in project.toml to a version of form 'X.Y'.

ERROR:    Application startup failed. Exiting.
```

### tests/fixtures/project_toml_api_version_missing

In the context of the production deploy self-check:

```term
Function failed validation: project.toml is missing the required 'com.salesforce.salesforce-api-version' key.
```

In the context of the CLI start command:

```term
Starting sf-functions-python v0.4.0 in single process mode.
INFO:     Started server process [81726]
INFO:     Waiting for application startup.
ERROR:    RuntimeError: Unable to load function: project.toml is missing the required 'com.salesforce.salesforce-api-version' key.

ERROR:    Application startup failed. Exiting.
```

### tests/fixtures/project_toml_api_version_too_old

In the context of the production deploy self-check:

```term
Function failed validation: Salesforce REST API version '52.1' is not supported. Update 'salesforce-api-version' in project.toml to '53.0' or newer.
```

In the context of the CLI start command:

```term
Starting sf-functions-python v0.4.0 in single process mode.
INFO:     Started server process [81728]
INFO:     Waiting for application startup.
ERROR:    RuntimeError: Unable to load function: Salesforce REST API version '52.1' is not supported. Update 'salesforce-api-version' in project.toml to '53.0' or newer.

ERROR:    Application startup failed. Exiting.
```

### tests/fixtures/project_toml_api_version_triple_digits

In the context of the production deploy self-check:

```term
Function failed validation: A main.py file was not found at: /Users/emorley/src/sf-functions-python/tests/fixtures/project_toml_api_version_triple_digits/main.py
```

In the context of the CLI start command:

```term
Starting sf-functions-python v0.4.0 in single process mode.
INFO:     Started server process [81730]
INFO:     Waiting for application startup.
ERROR:    RuntimeError: Unable to load function: A main.py file was not found at: /Users/emorley/src/sf-functions-python/tests/fixtures/project_toml_api_version_triple_digits/main.py

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
Function failed validation: A project.toml file was not found at: /Users/emorley/src/sf-functions-python/tests/fixtures/project_toml_file_missing/project.toml
```

In the context of the CLI start command:

```term
Starting sf-functions-python v0.4.0 in single process mode.
INFO:     Started server process [81734]
INFO:     Waiting for application startup.
ERROR:    RuntimeError: Unable to load function: A project.toml file was not found at: /Users/emorley/src/sf-functions-python/tests/fixtures/project_toml_file_missing/project.toml

ERROR:    Application startup failed. Exiting.
```

### tests/fixtures/project_toml_invalid_toml

In the context of the production deploy self-check:

```term
Function failed validation: project.toml is not valid TOML: Expected '=' after a key in a key/value pair (at line 1, column 4)
```

In the context of the CLI start command:

```term
Starting sf-functions-python v0.4.0 in single process mode.
INFO:     Started server process [81736]
INFO:     Waiting for application startup.
ERROR:    RuntimeError: Unable to load function: project.toml is not valid TOML: Expected '=' after a key in a key/value pair (at line 1, column 4)

ERROR:    Application startup failed. Exiting.
```

### tests/fixtures/project_toml_invalid_unicode

In the context of the production deploy self-check:

```term
Function failed validation: Could not read project.toml: UnicodeDecodeError: 'utf-8' codec can't decode byte 0x80 in position 0: invalid start byte
```

In the context of the CLI start command:

```term
Starting sf-functions-python v0.4.0 in single process mode.
INFO:     Started server process [81738]
INFO:     Waiting for application startup.
ERROR:    RuntimeError: Unable to load function: Could not read project.toml: UnicodeDecodeError: 'utf-8' codec can't decode byte 0x80 in position 0: invalid start byte

ERROR:    Application startup failed. Exiting.
```

### tests/fixtures/project_toml_salesforce_table_missing

In the context of the production deploy self-check:

```term
Function failed validation: project.toml is missing the required '[com.salesforce]' table.
```

In the context of the CLI start command:

```term
Starting sf-functions-python v0.4.0 in single process mode.
INFO:     Started server process [81740]
INFO:     Waiting for application startup.
ERROR:    RuntimeError: Unable to load function: project.toml is missing the required '[com.salesforce]' table.

ERROR:    Application startup failed. Exiting.
```

### tests/fixtures/project_toml_salesforce_table_wrong_type

In the context of the production deploy self-check:

```term
Function failed validation: project.toml is missing the required '[com.salesforce]' table.
```

In the context of the CLI start command:

```term
Starting sf-functions-python v0.4.0 in single process mode.
INFO:     Started server process [81742]
INFO:     Waiting for application startup.
ERROR:    RuntimeError: Unable to load function: project.toml is missing the required '[com.salesforce]' table.

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
invocationId=00DJS0000000123ABC-fa35b79dc4047411826d3c52071066b9 level=error msg="Exception occurred whilst executing function: ZeroDivisionError: division by zero"
```

### tests/fixtures/return_value_not_serializable

Server log:

```term
Starting sf-functions-python v0.4.0 in single process mode.
INFO:     Started server process [81754]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://localhost:8080 (Press CTRL+C to quit)
invocationId=00DJS0000000123ABC-0baf07e3d0f724a9b944165a86e51f89 level=error msg="Function return value cannot be serialized: TypeError: Type is not JSON serializable: set"
```

### Invalid CloudEvent payload (should not be possible to trigger this in practice)

Server log:

```term
Starting sf-functions-python v0.4.0 in single process mode.
INFO:     Started server process [81767]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://localhost:8080 (Press CTRL+C to quit)
level=error msg="Could not parse CloudEvent: Data payload is not valid JSON: invalid literal: line 1 column 1 (char 0)"
```
