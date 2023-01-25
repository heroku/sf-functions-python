from unittest.mock import patch

import pytest

from salesforce_functions import QueriedRecord, RecordQueryResult
from salesforce_functions.testing import mock_context, mock_event

# In the upstream template this import has to be an absolute import. However,
# for the testcase to work in this repository it must be a relative import.
from ..main import function


@pytest.mark.asyncio
async def test_function() -> None:
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
