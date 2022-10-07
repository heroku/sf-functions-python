import contextlib
import functools
from pathlib import Path
from typing import Any

from aiohttp import ClientSession, DummyCookieJar
from starlette.applications import Starlette
from starlette.config import Config
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
import orjson

from ..context import Context, Org, User
from ..data_api import DataAPI
from ..invocation_event import InvocationEvent
from .cloud_event import CloudEventError, SalesforceFunctionsCloudEvent
from .user_function import UserFunction, load_user_function


class OrjsonResponse(JSONResponse):
    def render(self, content: Any) -> bytes:
        return orjson.dumps(content)


# TODO: Figure out logging situation.
async def invoke(function: UserFunction, request: Request) -> OrjsonResponse:
    if request.headers.get("x-health-check", "").lower() == "true":
        return OrjsonResponse("OK")

    body = await request.body()

    try:
        cloudevent = SalesforceFunctionsCloudEvent.from_http(request.headers, body)
    except CloudEventError as e:
        return OrjsonResponse(f"Could not parse CloudEvent: {e}", status_code=400)

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
        function_result = await function(event, context)
    except Exception as e:
        # TODO: Should this include the traceback, or should that only be in x-extra-info's `stack`?
        return OrjsonResponse(
            f"Exception occurred whilst executing function: {e.__class__.__name__}: {e}",
            status_code=500,
        )

    # TODO: What should the response be if the function returns None? Currently a body of `null`.
    # if function_result is None:
    #     return Response(content=None, media_type="application/json")

    try:
        # TODO: Decide if we need to support the user serialising themselves?
        return OrjsonResponse(function_result)
    # TODO: Switch to more specific exception types
    except Exception as e:
        # TODO: Should this include the traceback, or should that only be in x-extra-info's `stack`?
        return OrjsonResponse(
            f"Function return value cannot be serialized: {e.__class__.__name__}: {e}",
            status_code=500,
        )


async def handle_error(request: Request, e: Exception) -> OrjsonResponse:
    return OrjsonResponse(f"Internal error: {e}", status_code=503)


@contextlib.asynccontextmanager
async def lifespan(app: Starlette):
    # Disable cookie storage using DummyCookieJar, given:
    # - The same session will be used by multiple invocation events.
    # - We don't need cookie support.
    async with ClientSession(cookie_jar=DummyCookieJar()) as aiohttp_session:
        app.state.aiohttp_session = aiohttp_session
        yield


config = Config()

# TODO: Should this be moved into lifespan and passed via `app.state` instead?
# `FUNCTION_PROJECT_PATH` is set by the CLI.
PROJECT_PATH = config("FUNCTION_PROJECT_PATH", cast=Path)
user_function = load_user_function(PROJECT_PATH)

# TODO: Remove debug=True
app = Starlette(
    debug=True,
    exception_handlers={Exception: handle_error},
    lifespan=lifespan,
    routes=[
        Route("/", functools.partial(invoke, user_function), methods=["POST"]),
    ],
)
