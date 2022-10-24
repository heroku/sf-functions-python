import contextlib
import sys
import traceback
from pathlib import Path
from typing import Any

import orjson
import structlog
from aiohttp import ClientSession, DummyCookieJar
from starlette.applications import Starlette
from starlette.config import Config
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from ..context import Context, Org, User
from ..data_api import DataAPI
from ..invocation_event import InvocationEvent
from .cloud_event import CloudEventError, SalesforceFunctionsCloudEvent
from .exceptions import LoadFunctionError
from .logging import configure_logging, get_logger
from .user_function import load_user_function

logger = get_logger()


class OrjsonResponse(JSONResponse):
    def render(self, content: Any) -> bytes:
        return orjson.dumps(content)


async def invoke(request: Request) -> OrjsonResponse:
    structlog.contextvars.clear_contextvars()

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
    except Exception as e:
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


async def handle_error(request: Request, e: Exception) -> OrjsonResponse:
    message = f"Internal error: {e.__class__.__name__}: {e}"
    logger.error(message)
    return OrjsonResponse(message, status_code=500)


@contextlib.asynccontextmanager
async def lifespan(app: Starlette):
    configure_logging()

    config = Config()
    # `FUNCTION_PROJECT_PATH` is set by the CLI.
    PROJECT_PATH = config("FUNCTION_PROJECT_PATH", cast=Path)

    try:
        app.state.user_function = load_user_function(PROJECT_PATH)
    except LoadFunctionError as e:
        # Print the original exception separately if we've chosen to propagate it, since we
        # want the full traceback for it to be shown, unlike for the exception raised below.
        if e.__cause__:
            print()
            traceback.print_exception(e.__cause__)
            print()

        # We cannot just log a crafted error message and `sys.exit(1)` like in the CLI's check_function(),
        # since we're running inside a coroutine managed by uvicorn. So instead we raise an exception and
        # suppress the unhelpful/unwanted traceback using `tracebacklimit`.
        sys.tracebacklimit = 0
        raise RuntimeError(f"Function failed to load! {e}") from None

    # Disable cookie storage using DummyCookieJar, given:
    # - The same session will be used by multiple invocation events.
    # - We don't need cookie support.
    async with ClientSession(cookie_jar=DummyCookieJar()) as aiohttp_session:
        app.state.aiohttp_session = aiohttp_session
        yield


app = Starlette(
    exception_handlers={Exception: handle_error},
    lifespan=lifespan,
    routes=[
        Route("/", invoke, methods=["POST"]),
    ],
)
