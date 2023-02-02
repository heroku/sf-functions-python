import contextlib
import os
import sys
import time
import traceback
from enum import Enum
from pathlib import Path
from typing import Any, AsyncGenerator

import orjson
import structlog
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route
from structlog.stdlib import BoundLogger

from ..context import Context, Org, User
from ..data_api import DataAPI, _create_session  # pyright: ignore [reportPrivateUsage]
from ..invocation_event import InvocationEvent
from .cloud_event import CloudEventError, SalesforceFunctionsCloudEvent
from .config import ConfigError, load_config
from .function_loader import Function, LoadFunctionError, load_function
from .logging import configure_logging, get_logger

PROJECT_PATH_ENV_VAR = "FUNCTION_PROJECT_PATH"


async def _handle_function_invocation(request: Request) -> Response:
    """Handle an incoming function invocation request."""
    structlog.contextvars.clear_contextvars()
    logger: BoundLogger = request.app.state.logger

    if request.headers.get("x-health-check", "").lower() == "true":
        return _make_response("OK", _StatusCode.SUCCESS)

    body = await request.body()

    try:
        cloudevent = SalesforceFunctionsCloudEvent.from_http(request.headers, body)
    except CloudEventError as e:
        message = f"Couldn't parse CloudEvent: {e}"
        logger.error(message)
        return _make_response(message, _StatusCode.REQUEST_ERROR, exception=e)

    structlog.contextvars.bind_contextvars(invocationId=cloudevent.id)

    event = InvocationEvent(
        id=cloudevent.id,
        type=cloudevent.type,
        source=cloudevent.source,
        data=cloudevent.data,
        time=cloudevent.time,
    )

    context = Context(
        org=Org(
            id=cloudevent.sf_context.user_context.org_id,
            base_url=cloudevent.sf_context.user_context.salesforce_base_url,
            domain_url=cloudevent.sf_context.user_context.org_domain_url,
            data_api=DataAPI(
                org_domain_url=cloudevent.sf_context.user_context.org_domain_url,
                api_version=request.app.state.salesforce_api_version,
                access_token=cloudevent.sf_function_context.access_token,
                session=request.app.state.data_api_session,
            ),
            user=User(
                id=cloudevent.sf_context.user_context.user_id,
                username=cloudevent.sf_context.user_context.username,
                on_behalf_of_user_id=cloudevent.sf_context.user_context.on_behalf_of_user_id,
            ),
        )
    )

    function: Function = request.app.state.function
    function_start_time_ns = time.perf_counter_ns()

    try:
        function_result = await function(event, context)
    except Exception as e:  # pylint: disable=broad-except
        message = (
            f"Exception occurred while executing function: {e.__class__.__name__}: {e}"
        )
        logger.exception(message)
        return _make_response(
            message,
            _StatusCode.FUNCTION_ERROR,
            cloudevent=cloudevent,
            function_duration_ns=time.perf_counter_ns() - function_start_time_ns,
            exception=e,
        )

    function_duration_ns = time.perf_counter_ns() - function_start_time_ns

    try:
        return _make_response(
            function_result,
            _StatusCode.SUCCESS,
            cloudevent=cloudevent,
            function_duration_ns=function_duration_ns,
        )
    except orjson.JSONEncodeError as e:
        message = (
            f"Function return value can't be serialized: {e.__class__.__name__}: {e}"
        )
        logger.error(message)
        return _make_response(
            message,
            _StatusCode.FUNCTION_ERROR,
            cloudevent=cloudevent,
            function_duration_ns=function_duration_ns,
            exception=e,
        )


async def _handle_internal_error(request: Request, exception: Exception) -> Response:
    logger: BoundLogger = request.app.state.logger
    message = f"Internal error: {exception.__class__.__name__}: {exception}"
    logger.exception(message)
    return _make_response(message, _StatusCode.INTERNAL_ERROR, exception=exception)


class _StatusCode(Enum):
    SUCCESS = 200
    REQUEST_ERROR = 400
    FUNCTION_ERROR = 500
    INTERNAL_ERROR = 503


def _make_response(
    content: Any,
    status_code: _StatusCode,
    cloudevent: SalesforceFunctionsCloudEvent | None = None,
    function_duration_ns: int | None = None,
    exception: Exception | None = None,
) -> Response:
    # Based on the `responseExtraInfo` definition in:
    # https://github.com/forcedotcom/sf-fx-schema/blob/main/schema.json
    metadata: dict[str, str | int | bool] = {
        "requestId": cloudevent.id if cloudevent else "n/a",
        "source": cloudevent.source if cloudevent else "n/a",
        "statusCode": status_code.value,
    }

    if function_duration_ns:
        metadata["execTimeMs"] = round(function_duration_ns / (1000 * 1000))

    if exception:
        metadata["stack"] = "".join(traceback.format_exception(exception))
        metadata["isFunctionError"] = status_code == _StatusCode.FUNCTION_ERROR

    # We're not using Starlette's `JSONResponse`, since it uses the Python stdlib's
    # `json` module for JSON serialization, whereas `orjson` has better performance:
    # https://github.com/ijl/orjson#performance
    return Response(
        content=orjson.dumps(content),
        media_type="application/json",
        status_code=status_code.value,
        headers={
            "x-extra-info": orjson.dumps(metadata).decode(),
        },
    )


@contextlib.asynccontextmanager
async def _lifespan(app: Starlette) -> AsyncGenerator[None, None]:
    """
    Asynchronous context manager for handling app setup/teardown.

    Anything before the `yield` will be run before the app starts serving
    requests, and anything after will be run when the server shuts down.
    """
    configure_logging()
    app.state.logger = get_logger()

    # This env var is set by the CLI, as a way to propagate CLI args to the ASGI app.
    project_path = Path(os.environ[PROJECT_PATH_ENV_VAR])

    try:
        config = load_config(project_path)
        app.state.function = load_function(project_path)
    except (ConfigError, LoadFunctionError) as e:
        # We cannot log an error message and `sys.exit(1)` like in the CLI's `check_function()`,
        # since we're running inside a uvicorn-managed coroutine. So instead, we raise an
        # exception and suppress the unwanted traceback using `tracebacklimit`.
        sys.tracebacklimit = 0
        raise RuntimeError(f"Unable to load function: {e}") from None

    app.state.salesforce_api_version = config.salesforce_api_version

    async with _create_session() as data_api_session:
        app.state.data_api_session = data_api_session
        yield


# The ASGI app that will be run by uvicorn.
asgi_app = Starlette(
    exception_handlers={Exception: _handle_internal_error},
    lifespan=_lifespan,
    routes=[
        Route("/", _handle_function_invocation, methods=["POST"]),
    ],
)
