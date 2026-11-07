from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import aiohttp
import pytest

from provider_requesting.events_providers import (
    EventsPaginator,
    EventsProviderHTTPClient,
)
from provider_requesting.schemas import (
    EventRegister,
    EventResponse,
    EventsResponse,
    PlaceResponse,
)


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

    client = EventsProviderHTTPClient(
        session=mock_session,
        api_key="test-api-key"
    )
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

    client = EventsProviderHTTPClient(
        session=mock_session,
        api_key="test-api-key"
    )
    register_data = EventRegister(
        event_id=uuid4(),
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

    client = EventsProviderHTTPClient(
        session=mock_session,
        api_key="test-api-key"
    )

    with pytest.raises(aiohttp.ClientResponseError):
        await client.get_events(changed_at=datetime.now(UTC))


def _make_event_response(name: str = 'Event') -> EventResponse:
    now = datetime.now(UTC)
    return EventResponse(
        id=uuid4(),
        name=name,
        place=PlaceResponse(
            id=uuid4(),
            name='Place',
            city='Moscow',
            address='Address 1',
            seats_pattern='A1-10',
            changed_at=now,
            created_at=now,
        ),
        event_time=now,
        registration_deadline=now,
        status='published',
        number_of_visitors=5,
        changed_at=now,
        created_at=now,
        status_changed_at=now,
    )


@pytest.mark.asyncio
async def test_events_paginator_single_page():
    changed_at = datetime(2000, 1, 1, tzinfo=UTC)
    event_1 = _make_event_response('Event 1')
    event_2 = _make_event_response('Event 2')

    mock_client = AsyncMock()
    mock_client.get_events.return_value = EventsResponse(
        next=None,
        previous=None,
        results=[event_1, event_2],
    )

    paginator = EventsPaginator(client=mock_client, changed_at=changed_at)
    items = [event async for event in paginator]

    assert items == [event_1, event_2]
    mock_client.get_events.assert_awaited_once_with(
        changed_at=changed_at,
        next_url=None,
    )


@pytest.mark.asyncio
async def test_events_paginator_multiple_pages():
    changed_at = datetime(2000, 1, 1, tzinfo=UTC)
    event_1 = _make_event_response('Event 1')
    event_2 = _make_event_response('Event 2')
    event_3 = _make_event_response('Event 3')

    next_url = 'http://provider/api/events/?cursor=page2'

    page_1 = EventsResponse(
        next=next_url,
        previous=None,
        results=[event_1, event_2],
    )
    page_2 = EventsResponse(
        next=None,
        previous='http://provider/api/events/?cursor=page1',
        results=[event_3],
    )

    mock_client = AsyncMock()
    mock_client.get_events.side_effect = [page_1, page_2]

    paginator = EventsPaginator(client=mock_client, changed_at=changed_at)
    items = [event async for event in paginator]

    assert items == [event_1, event_2, event_3]
    assert mock_client.get_events.await_count == 2
    mock_client.get_events.assert_any_await(
        changed_at=changed_at,
        next_url=None,
    )
    mock_client.get_events.assert_any_await(
        changed_at=changed_at,
        next_url=next_url,
    )


@pytest.mark.asyncio
async def test_events_paginator_empty_results():
    changed_at = datetime(2026, 1, 1, tzinfo=UTC)

    mock_client = AsyncMock()
    mock_client.get_events.return_value = EventsResponse(
        next=None,
        previous=None,
        results=[],
    )

    paginator = EventsPaginator(client=mock_client, changed_at=changed_at)
    items = [event async for event in paginator]

    assert items == []
    mock_client.get_events.assert_awaited_once_with(
        changed_at=changed_at,
        next_url=None,
    )
