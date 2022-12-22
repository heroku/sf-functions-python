import os
import sys
from argparse import ArgumentParser
from pathlib import Path

import uvicorn

from ..__version__ import __version__
from .app import PROJECT_PATH_ENV_VAR
from .config import ConfigError, load_config
from .function_loader import LoadFunctionError, load_function

PROGRAM_NAME = "sf-functions-python"
ASGI_APP_IMPORT_STRING = "salesforce_functions._internal.app:app"


def main(args: list[str] | None = None) -> int:
    parser = ArgumentParser(
        prog=PROGRAM_NAME,
        description="Salesforce Functions Python Runtime",
        allow_abbrev=False,
    )
    subparsers = parser.add_subparsers(
        required=True,
        dest="subcommand",
        title="subcommands",
    )

    # Subcommand `check`
    parser_check = subparsers.add_parser(
        "check", help="Checks that a function project is configured correctly"
    )
    parser_check.add_argument(
        "project_path",
        metavar="<project-path>",
        type=Path,
        help="The directory that contains the function",
    )

    # Subcommand `serve`
    parser_serve = subparsers.add_parser(
        "serve", help="Serves a function project via HTTP"
    )
    parser_serve.add_argument(
        "project_path",
        metavar="<project-path>",
        type=Path,
        help="The directory that contains the function",
    )
    parser_serve.add_argument(
        "--host",
        default="localhost",
        help="The host on which the web server should bind (default: %(default)s)",
    )
    parser_serve.add_argument(
        "-p",
        "--port",
        default=8080,
        type=int,
        help="The port on which the web server should listen (default: %(default)s)",
    )
    parser_serve.add_argument(
        "-w",
        "--workers",
        default=1,
        type=int,
        help="The number of worker processes (default: %(default)s)",
    )

    # Subcommand `version`
    parser_check = subparsers.add_parser(
        "version", help="Prints the version of the Python Functions Runtime"
    )

    parsed_args = parser.parse_args(args=args)

    match parsed_args.subcommand:
        case "check":
            return check_function(parsed_args.project_path)
        case "serve":
            return start_server(
                parsed_args.project_path,
                parsed_args.host,
                parsed_args.port,
                parsed_args.workers,
            )
        case "version":
            print(__version__)
            return 0
        case other:  # pragma: no cover
            # This is only reachable in the case of the parser config being out of sync,
            # since argparse handles the user providing invalid subcommands for us.
            raise NotImplementedError(f"Unhandled subcommand '{other}'")


def check_function(project_path: Path) -> int:
    try:
        load_config(project_path)
        load_function(project_path)
    except (ConfigError, LoadFunctionError) as e:
        print(f"Function failed validation: {e}", file=sys.stderr)
        return 1

    print("Function passed validation")
    return 0


def start_server(project_path: Path, host: str, port: int, workers: int) -> int:
    if workers == 1:
        process_mode = "single process mode"
    else:
        process_mode = f"multi-process mode ({workers} worker processes)"

    print(f"Starting {PROGRAM_NAME} v{__version__} in {process_mode}.")

    # Propagate CLI args to the ASGI app (uvicorn doesn't support passing custom config directly).
    os.environ[PROJECT_PATH_ENV_VAR] = str(project_path)

    try:
        # This only ever returns in the case of a successful shutdown (from a SIGINT/SIGTERM).
        # If errors occur, uvicorn will catch/log them and call `sys.exit()` itself.
        uvicorn.run(  # pyright: ignore [reportUnknownMemberType]
            ASGI_APP_IMPORT_STRING,
            host=host,
            port=port,
            workers=workers,
            access_log=False,
        )
    finally:
        # Prevent the env var from leaking into the caller, for example during tests.
        del os.environ[PROJECT_PATH_ENV_VAR]

    return 0
