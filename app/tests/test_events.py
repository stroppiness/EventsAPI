from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import aiohttp
import pytest

from provider_requesting.events_providers import EventsProviderHTTPClient
from provider_requesting.schemas import EventRegister


def _mock_aiohttp_response(status: int, json_data: dict):
    """Мокирует контекстный менеджер, который возвращает session.get/post."""
    mock_response = MagicMock()
    mock_response.status = status
    mock_response.json = AsyncMock(return_value=json_data)
    mock_response.raise_for_status = MagicMock()

    mock_context_manager = MagicMock()
    mock_context_manager.__aenter__.return_value = mock_response
    return mock_context_manager


@pytest.mark.asyncio
async def test_get_events_success():
    mock_session = MagicMock()
    mock_session.get.return_value = _mock_aiohttp_response(
        200, {"next": None, "previous": None, "results": []}
    )

    client = EventsProviderHTTPClient(session=mock_session, api_key="test-api-key")
    result = await client.get_events(changed_at=datetime.now(UTC))

    assert result.results == []
    mock_session.get.assert_called_once()


@pytest.mark.asyncio
async def test_register_event_success():
    mock_session = MagicMock()
    expected_ticket_id = uuid4()

    mock_session.post.return_value = _mock_aiohttp_response(
        201, {"ticket_id": str(expected_ticket_id)}
    )

    client = EventsProviderHTTPClient(session=mock_session, api_key="test-api-key")
    register_data = EventRegister(
        first_name="Алексей",
        last_name="Петров",
        seat="B5",
        email="alex@example.com",
    )

    result = await client.register(event_id=uuid4(), data=register_data)

    assert result.ticket_id == expected_ticket_id
    mock_session.post.assert_called_once()


@pytest.mark.asyncio
async def test_get_events_http_error():
    mock_session = MagicMock()

    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = aiohttp.ClientResponseError(
        request_info=MagicMock(),
        history=(),
        status=500,
        message="Internal Server Error",
    )

    mock_context_manager = MagicMock()
    mock_context_manager.__aenter__.return_value = mock_response
    mock_session.get.return_value = mock_context_manager

    client = EventsProviderHTTPClient(session=mock_session, api_key="test-api-key")

    with pytest.raises(aiohttp.ClientResponseError):
        await client.get_events(changed_at=datetime.now(UTC))
