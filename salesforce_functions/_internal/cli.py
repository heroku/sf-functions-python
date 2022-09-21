import os
import sys
from argparse import ArgumentParser
from pathlib import Path
from typing import Optional

from ..__version__ import __version__
from .exceptions import SalesforceFunctionError


def main(command_name: Optional[str] = None):
    parser = ArgumentParser(
        prog=command_name,
        description="Salesforce Functions Python Runtime",
        allow_abbrev=False,
    )
    subparsers = parser.add_subparsers(
        required=True,
        dest="subcommand",
        title="subcommands",
        help="Available subcommands",
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

    args = parser.parse_args()
    match args.subcommand:
        case "check":
            check_function(args.project_path)
        case "serve":
            start_server(args.project_path, args.host, args.port, args.workers)
        case "version":
            print(__version__)
        case other:
            # This is only reached in the case of the parser config being out of sync,
            # since argparse handles the user providing invalid subcommands for us.
            raise NotImplementedError(f"Unhandled subcommand '{other}'")


def check_function(project_path: Path):
    from .user_function import load_user_function

    try:
        load_user_function(project_path)
        # TODO: Clean this up
        print("Function is valid")
    except SalesforceFunctionError as e:
        # TODO: Clean up wording + decide whether to switch to a more specific exception type.
        print(f"Unable to load function: {e}", file=sys.stderr)
        sys.exit(1)


def start_server(project_path: Path, host: str, port: int, workers: int):
    import uvicorn  # pyright: ignore [reportMissingTypeStubs]

    # Propagate CLI args to the ASGI app using env vars (there sadly isn't a better way to do this).
    os.environ["FUNCTION_PROJECT_PATH"] = str(project_path)

    try:
        uvicorn.run(  # pyright: ignore [reportUnknownMemberType]
            "salesforce_functions._internal.app:app",
            host=host,
            port=port,
            workers=workers,
            access_log=False,
        )
    except SalesforceFunctionError as e:
        # TODO: Clean up wording + decide whether to switch to a more specific exception type.
        print(f"Unable to serve function: {e}", file=sys.stderr)
        sys.exit(1)
