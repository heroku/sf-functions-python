import contextlib
import sys
from typing import Any, AsyncGenerator

import orjson
import structlog
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from structlog.stdlib import BoundLogger

from ..context import Context, Org, User
from ..data_api import DataAPI
from ..invocation_event import InvocationEvent
from . import config
from .cloud_event import CloudEventError, SalesforceFunctionsCloudEvent
from .function_loader import LoadFunctionError, load_function
from .logging import configure_logging, get_logger


class OrjsonResponse(JSONResponse):
    """
    Wrapper around Starlette's `JSONResponse` to use an alternative library for JSON serialisation.

    Used since `orjson` has much better performance than the Python stdlib's `json` module:
    https://github.com/ijl/orjson#performance
    """

    def render(self, content: Any) -> bytes:
        return orjson.dumps(content)


async def invoke(request: Request) -> OrjsonResponse:
    """Handle an incoming function invocation request."""
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
        time=cloudevent.time,
    )

    context = Context(
        org=Org(
            id=cloudevent.sf_context.user_context.org_id,
            base_url=cloudevent.sf_context.user_context.salesforce_base_url,
            domain_url=cloudevent.sf_context.user_context.org_domain_url,
            data_api=DataAPI(
                cloudevent.sf_context.user_context.org_domain_url,
                # TODO: This should be the API version in project.toml instead
                cloudevent.sf_context.api_version,
                cloudevent.sf_function_context.access_token,
                session=request.app.state.data_api_session,
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
async def lifespan(app: Starlette) -> AsyncGenerator[None, None]:
    """
    Asynchronous context manager for handling app setup/teardown.

    Anything before the `yield` will be run before the app starts serving
    requests, and anything after will be run when the server shuts down.
    """
    configure_logging()
    # `get_logger()` returns a proxy that only instantiates the logger on first usage.
    # Calling `bind()` here ensures that this instantiation doesn't have to occur each
    # time the function is invoked.
    app.state.logger = get_logger().bind()

    try:
        app.state.user_function = load_function(config.project_path())
    except LoadFunctionError as e:
        # We cannot log an error message and `sys.exit(1)` like in the CLI's `check_function()`,
        # since we're running inside a uvicorn-managed coroutine. So instead, we raise an
        # exception and suppress the unwanted traceback using `tracebacklimit`.
        sys.tracebacklimit = 0
        raise RuntimeError(f"Function failed to load! {e}") from None

    async with (
        DataAPI._create_session()  # pyright: ignore [reportPrivateUsage] pylint:disable=protected-access
    ) as data_api_session:
        app.state.data_api_session = data_api_session
        yield


# The ASGI app that will be run by uvicorn.
app = Starlette(
    exception_handlers={Exception: handle_internal_error},
    lifespan=lifespan,
    routes=[
        Route("/", invoke, methods=["POST"]),
    ],
)
