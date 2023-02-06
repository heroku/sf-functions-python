"""
Testing utilities for Python Salesforce Functions.

This example shows how to create a Python unit test to test your function. To mimic
access to the Salesforce org, it first creates a mock `InvocationEvent` (with an empty
data payload) and a mock `Context`. Next, it builds a mock query that returns a single
record from the `Account` Salesforce object. Using the mock event and context, it
executes the function and finally asserts that the result equals the `QueriedRecord`
that you expect.

```python
from unittest.mock import patch

import pytest
from salesforce_functions import QueriedRecord, RecordQueryResult
from salesforce_functions.testing import mock_context, mock_event

from main import function


@pytest.mark.asyncio
async def test_function():
    event = mock_event(data=None)
    context = mock_context()

    with patch.object(context.org.data_api, "query") as mock_query:
        mock_query.return_value = RecordQueryResult(
            done=True,
            total_size=1,
            records=[
                QueriedRecord(type="Account", fields={"Name": "Example Account"}),
            ],
            next_records_url=None,
        )
        result = await function(event, context)

    assert result == [
        QueriedRecord(type="Account", fields={"Name": "Example Account"}),
    ]
```
"""

from datetime import datetime
from typing import TypeVar
from uuid import uuid4

from salesforce_functions import Context, InvocationEvent, Org, User
from salesforce_functions.data_api import DataAPI

T = TypeVar("T")


def mock_event(
    *,
    data: T,
    id: str | None = None,  # pylint: disable=redefined-builtin
    type: str = "com.salesforce.function.invoke.sync",  # pylint: disable=redefined-builtin
    source: str = "urn:event:from:salesforce/JS/56.0/00DJS0000000123ABC/apex/ExampleClass:example_function():7",
    time: datetime | None = None,
) -> InvocationEvent[T]:
    """
    Create an example `InvocationEvent` instance for use in unit tests.

    The `data` parameter is required, and is the input data payload of the event.

    For example:

    ```python
    event = mock_event(data={"customer_id": "1234"})

    result = await function(event, context)
    ```
    """
    return InvocationEvent(
        id=id if id is not None else str(uuid4()),
        type=type,
        source=source,
        data=data,
        time=time if time is not None else datetime.today(),
    )


def mock_context(
    *,
    org_id: str = "00DJS0000000123ABC",
    org_domain_url: str = "https://example-domain-url.my.salesforce.tld",
    user_id: str = "005JS000000H123",
    username: str = "user@example.tld",
    on_behalf_of_user_id: str = "005JS000000H456",
    client_api_version: str = "56.0",
) -> Context:
    """
    Create an example `Context` instance for use in unit tests.

    For example:

    ```python
    context = mock_context()

    result = await function(event, context)
    ```

    If the function uses `context.org.data_api`, it will need patching separately, inside
    the unit test. See the example in the `testing` module overview for more information.
    """
    return Context(
        org=Org(
            id=org_id,
            base_url=org_domain_url,
            domain_url=org_domain_url,
            data_api=DataAPI(
                org_domain_url=org_domain_url,
                api_version=client_api_version,
                access_token="EXAMPLE-TOKEN",
            ),
            user=User(
                id=user_id,
                username=username,
                on_behalf_of_user_id=on_behalf_of_user_id,
            ),
        )
    )
