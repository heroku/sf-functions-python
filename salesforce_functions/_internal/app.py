import contextlib
import os
import sys
from pathlib import Path
from typing import Any

import orjson
import structlog
from aiohttp import ClientSession, DummyCookieJar
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from structlog.stdlib import BoundLogger

from ..context import Context, Org, User
from ..data_api import DataAPI
from ..invocation_event import InvocationEvent
from .cloud_event import CloudEventError, SalesforceFunctionsCloudEvent
from .function_loader import load_function, LoadFunctionError
from .logging import configure_logging, get_logger


class OrjsonResponse(JSONResponse):
    def render(self, content: Any) -> bytes:
        return orjson.dumps(content)


async def invoke(request: Request) -> OrjsonResponse:
    structlog.contextvars.clear_contextvars()
    logger: BoundLogger = request.app.state.logger

    if request.headers.get("x-health-check", "").lower() == "true":
        return OrjsonResponse("OK")

    body = await request.body()

    try:
        cloudevent = SalesforceFunctionsCloudEvent.from_http(request.headers, body)
    except CloudEventError as e:
        # TODO: Should the invocation ID be extracted manually for this error message?
        message = f"Could not parse CloudEvent: {e}"
        logger.error(message)
        return OrjsonResponse(message, status_code=400)

    structlog.contextvars.bind_contextvars(invocationId=cloudevent.id)

    event = InvocationEvent(
        id=cloudevent.id,
        type=cloudevent.type,
        source=cloudevent.source,
        data=cloudevent.data,
        data_content_type=cloudevent.data_content_type,
        data_schema=cloudevent.data_schema,
        time=cloudevent.time,
    )

    salesforce_base_url = cloudevent.sf_context.user_context.salesforce_base_url
    # TODO: This should be the API version in project.toml instead
    api_version = cloudevent.sf_context.api_version

    context = Context(
        org=Org(
            id=cloudevent.sf_context.user_context.org_id,
            base_url=salesforce_base_url,
            domain_url=cloudevent.sf_context.user_context.org_domain_url,
            api_version=api_version,
            data_api=DataAPI(
                salesforce_base_url,
                api_version,
                cloudevent.sf_function_context.access_token,
                request.app.state.aiohttp_session,
            ),
            user=User(
                id=cloudevent.sf_context.user_context.user_id,
                username=cloudevent.sf_context.user_context.username,
                on_behalf_of_user_id=cloudevent.sf_context.user_context.on_behalf_of_user_id,
            ),
        )
    )

    try:
        function_result = await app.state.user_function(event, context)
    except Exception as e:  # pylint: disable=broad-except
        message = (
            f"Exception occurred whilst executing function: {e.__class__.__name__}: {e}"
        )
        logger.exception(message)
        return OrjsonResponse(message, status_code=500)

    try:
        return OrjsonResponse(function_result)
    except orjson.JSONEncodeError as e:
        message = (
            f"Function return value cannot be serialized: {e.__class__.__name__}: {e}"
        )
        logger.error(message)
        return OrjsonResponse(message, status_code=500)


async def handle_internal_error(request: Request, e: Exception) -> OrjsonResponse:
    message = f"Internal error: {e.__class__.__name__}: {e}"
    request.app.state.logger.error(message)
    return OrjsonResponse(message, status_code=500)


@contextlib.asynccontextmanager
async def lifespan(app: Starlette):
    configure_logging()
    # `get_logger()` returns a proxy that only instantiates the logger on first usage.
    # Calling `bind()` here ensures that this instantiation doesn't have to occur each
    # time the function is invoked.
    app.state.logger = get_logger().bind()

    # Config passed down from the CLI.
    project_path = Path(os.environ["FUNCTION_PROJECT_PATH"])

    try:
        app.state.user_function = load_function(project_path)
    except LoadFunctionError as e:
        # We cannot log an error message and `sys.exit(1)` like in the CLI's `check_function()`,
        # since we're running inside a uvicorn-managed coroutine. So instead, we raise an
        # exception and suppress the unwanted traceback using `tracebacklimit`.
        sys.tracebacklimit = 0
        raise RuntimeError(f"Function failed to load! {e}") from None

    # Disable cookie storage using `DummyCookieJar`, given that:
    # - The same session will be used by multiple invocation events.
    # - We don't need cookie support.
    async with ClientSession(cookie_jar=DummyCookieJar()) as aiohttp_session:
        app.state.aiohttp_session = aiohttp_session
        yield


app = Starlette(
    exception_handlers={Exception: handle_internal_error},
    lifespan=lifespan,
    routes=[
        Route("/", invoke, methods=["POST"]),
    ],
)
