import logging
import typing
from collections import deque
from datetime import datetime
from uuid import UUID

import aiohttp

from provider_requesting.schemas import (
    EventCreated,
    EventRegister,
    EventResponse,
    EventsResponse,
    ProviderSeatsResponse,
    UnregisterResponse,
)

logger = logging.getLogger(__name__)


class EventsProviderClient(typing.Protocol):
    '''Класс для описания контрактов.'''

    async def register(
        self,
        event_id: UUID,
        data: EventRegister,
    ) -> EventCreated: ...

    async def get_events(
        self,
        changed_at: datetime,
        next_url: str | None = None,
    ) -> EventsResponse: ...

    async def unregister(
        self,
        event_id: UUID,
        ticket_id: UUID,
    ) -> UnregisterResponse: ...


class EventsPaginator:
    """Асинхронный итератор для постраничного получения событий."""

    def __init__(
        self,
        client: EventsProviderClient,
        changed_at: datetime,
    ) -> None:
        self.client = client
        self.changed_at = changed_at
        self._buffer: deque[EventResponse] = deque()
        self._next_url: str | None = None
        self._is_first_page: bool = True
        self._exhausted: bool = False

    def __aiter__(self) -> 'EventsPaginator':
        return self

    async def __anext__(self) -> EventResponse:
        while not self._buffer:
            if self._exhausted:
                raise StopAsyncIteration

            page = await self.client.get_events(
                changed_at=self.changed_at,
                next_url=None if self._is_first_page else self._next_url,
            )
            self._is_first_page = False

            self._buffer.extend(page.results)
            self._next_url = page.next

            if self._next_url is None:
                self._exhausted = True

        return self._buffer.popleft()


class EventsProviderHTTPClient:
    '''Класс для операций, требующих взимодействия с API-провайдером.'''

    def __init__(self, session: aiohttp.ClientSession, api_key: str):
        self.session = session
        self.api_key = api_key

    async def get_events(
        self,
        changed_at: datetime,
        next_url: str | None = None,
    ) -> EventsResponse:

        url = next_url or '/api/events/'
        params = {
            'changed_at': changed_at.strftime('%Y-%m-%d')
            } if next_url is None else None

        try:
            async with self.session.get(
                url,
                params=params,
                headers={'x-api-key': self.api_key},
            ) as response:

                response.raise_for_status()
                data = await response.json()

                return EventsResponse.model_validate(data)

        except aiohttp.ClientResponseError:
            logger.exception('Ошибка HTTP при обращении к Events Provider')
            raise

        except aiohttp.ClientError:
            logger.exception('Ошибка соединения с Events Provider')
            raise

    async def get_available_seats(
        self,
        event_id: UUID,
    ) -> ProviderSeatsResponse:
        url = f'/api/events/{event_id}/seats/'
        try:
            async with self.session.get(
                url,
                headers={'x-api-key': self.api_key},
            ) as response:
                response.raise_for_status()
                data = await response.json()
                return ProviderSeatsResponse.model_validate(data)
        except aiohttp.ClientResponseError:
            logger.exception(
                'Ошибка HTTP при получении мест у Events Provider')
            raise
        except aiohttp.ClientError:
            logger.exception('Ошибка соединения с Events Provider')
            raise

    async def register(
        self,
        event_id: UUID,
        data: EventRegister,
    ) -> EventCreated:

        url = f'/api/events/{event_id}/register/'

        try:
            async with self.session.post(
                url,
                headers={'x-api-key': self.api_key},
                json=data.model_dump(mode='json'),
            ) as response:
                response.raise_for_status()
                response_data = await response.json()

                return EventCreated.model_validate(response_data)

        except aiohttp.ClientResponseError:
            logger.exception('Ошибка HTTP при регистрации на мероприятие')
            raise

        except aiohttp.ClientError:
            logger.exception('Ошибка соединения с Events Provider')
            raise

    async def unregister(
        self,
        event_id: UUID,
        ticket_id: UUID,
    ) -> UnregisterResponse:
        url = f'/api/events/{event_id}/unregister/'

        try:
            async with self.session.delete(
                url,
                headers={'x-api-key': self.api_key},
                json={'ticket_id': str(ticket_id)},
            ) as response:
                response.raise_for_status()
                response_data = await response.json()

                return UnregisterResponse.model_validate(response_data)

        except aiohttp.ClientResponseError:
            logger.exception('Ошибка HTTP при отмене регистрации у Provider')
            raise

        except aiohttp.ClientError:
            logger.exception('Ошибка соединения с Events Provider')
            raise
