import logging
import os
import time
import typing
from datetime import datetime
from uuid import UUID, uuid4

import aiohttp
from dotenv import load_dotenv
from provider_requesting.schemas import (EventCreated, EventRegister,
                                         EventResponse, EventsResponse,
                                         PlaceEventsRepositoryApi,
                                         ProviderSeatsResponse, SeatsResponse)

load_dotenv()

logger = logging.getLogger(__name__)

API_KEY = os.getenv('API_KEY')


class EventsProviderClient(typing.Protocol):
    """Класс для описания контрактов."""

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

    async def get_all_events(
        self,
        changed_at: datetime,
    ) -> list[EventResponse]: ...


class EventsProviderHTTPClient:
    """Класс для операций, требующих взимодействия с API-провайдером."""

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
            'changed_at': changed_at.isoformat()} if next_url is None else None

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

    async def get_all_events(self, changed_at: datetime) -> list[EventResponse]:
        events = []
        next_url = None

        while True:
            page = await self.get_events(
                changed_at=changed_at,
                next_url=next_url,
            )

            events.extend(page.results)

            if page.next is None:
                break

            next_url = page.next

        return events

    async def get_available_seats(
        self,
        event_id: UUID,
    ) -> ProviderSeatsResponse:

        url = f"/api/events/{event_id}/seats/"

        async with self.session.get(
            f"{self.base_url}{url}",
            headers={"x-api-key": self.api_key},
        ) as response:
            response.raise_for_status()
            data = await response.json()

        return ProviderSeatsResponse(**data)

    async def register(
        self,
        event_id: UUID,
        data: EventRegister,
    ) -> EventCreated:

        async with self.session.post(
            f'/api/events/{event_id}/register/',
            headers={'x-api-key': self.api_key},
            json=data.model_dump(mode='json'),
        ) as response: ...


class SeatsService:
    CACHE_TTL = 30

    def __init__(
        self,
        repository: PlaceEventsRepositoryApi,
        provider_client: EventsProviderHTTPClient,
    ):
        self.repository = repository
        self.provider_client = provider_client
        self.cache = {}

    async def get_available_seats(
        self,
        event_id: UUID,
    ) -> SeatsResponse | None:

        event = await self.repository.get_event_by_id(event_id)

        if event is None:
            return None

        if event.status != "published":
            raise ValueError("Event is not published")

        cached_data = self.cache.get(event_id)

        if cached_data is not None:
            cached_at, seats = cached_data

            if time.monotonic() - cached_at < self.CACHE_TTL:
                return SeatsResponse(
                    event_id=event_id,
                    available_seats=seats,
                )

        provider_response = await self.provider_client.get_available_seats(
            event_id,
        )

        seats = provider_response.seats

        self.cache[event_id] = (time.monotonic(), seats)

        return SeatsResponse(
            event_id=event_id,
            available_seats=seats,
        )



class CreateTicketUsecase:
    def __init__(
        self,
        client: EventsProviderClient,
        events: EventRepository,
        tickets: TicketRepository,
    ):

        async def do(self, event_id: str, first_name: str, seat: str):
            event = await self.events.get(event_id)
            if not event:
                raise EventNotFound

            if not event.status == EventStatus.published:
                raise EventUnexpectedStatus

            ticket_id = await self.client.register(event.id, first_name, seat)

            await self.tickets.create(event.id, ticket_id, first_name)
