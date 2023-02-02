from dataclasses import dataclass
from datetime import datetime
from typing import Generic, TypeVar

__all__ = ["InvocationEvent"]

T = TypeVar("T")


@dataclass(frozen=True, kw_only=True, slots=True)
class InvocationEvent(Generic[T]):
    """
    The metadata and data payload of the event that caused the function to be invoked.

    The `InvocationEvent` type accepts a single generic parameter, which represents
    the type of the input data payload present in the `data` field.

    To improve IDE auto-completion and linting coverage, we recommend that you pass an
    explicit type in the type definition that represents the data payload the function
    expects to receive.

    For example, if your function must accept JSON input like this:

    ```json
    {
      "fieldOne": "Hello World!",
      "fieldTwo": 23
    }
    ```

    Then use these Python type annotations:

    ```python
    EventPayloadType = dict[str, Any]

    async def function(event: InvocationEvent[EventPayloadType], context: Context):
        # ...
    ```

    For more information, see the [Python typing documentation](https://docs.python.org/3/library/typing.html).
    """

    id: str
    """
    The unique identifier for this execution of the function.

    For example: `00DJS0000000123ABC-d75b3b6ece5011dcabbed4-3c6f7179`
    """
    type: str
    """
    The type of this invocation event.

    For example: `com.salesforce.function.invoke.sync`
    """
    source: str
    """
    A URI which identifies the context in which an event happened.

    This URI often includes information such as the type of the event source, the
    org publishing the event, or the process that produced the event.

    For example: `urn:event:from:salesforce/JS/56.0/00DJS0000000123ABC/apex/ExampleClass:example_function():7`
    """
    data: T
    """
    The input data payload of the event.

    The type of this field is determined from the generic type parameter passed
    to `InvocationEvent`.

    For example, `data` will be of type `dict[str, Any]` if the invocation event type is defined as:

    ```python
    InvocationEvent[dict[str, Any]]
    ```
    """
    time: datetime | None
    """
    The timestamp of when the occurrence happened.

    If the time of the occurrence can't be determined, then this attribute
    may be set to some other time (such as the current time).
    """
