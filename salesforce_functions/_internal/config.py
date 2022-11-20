import os
from pathlib import Path

PROJECT_PATH_ENV_VAR = "FUNCTION_PROJECT_PATH"


def project_path() -> Path:
    # This env var is set by the CLI as a way to propagate config to the ASGI app.
    return Path(os.environ[PROJECT_PATH_ENV_VAR])
