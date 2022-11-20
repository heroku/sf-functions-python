import os
from pathlib import Path
from unittest.mock import patch

from salesforce_functions._internal.config import PROJECT_PATH_ENV_VAR, project_path


def test_project_path() -> None:
    path = "path/to/function"

    with patch.dict(os.environ, {PROJECT_PATH_ENV_VAR: path}):
        assert project_path() == Path(path)
