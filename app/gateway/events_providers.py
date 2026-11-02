import os
import typing
import aiohttp

from datetime import datetime
from dotenv import load_dotenv
from uuid import UUID, uuid4

from app.gateway.schemas import EventCreated, EventsResponse, EventRegister

load_dotenv()

API_KEY = os.getenv('API_KEY')

class EventsProviderClient(typing.Protocol):
    async def register(
        self,
        event_id: UUID,
        data: EventRegister,
    ) -> EventCreated: ...

    async def get_events(self, date: datetime) -> EventsResponse: ...


class EventsProviderHTTPClient:
    def __init__(self, session: aiohttp.ClientSession, api_key: str):
        self.session = session
        self.api_key = api_key

    async def get_events(
        self,
        date: datetime,
    ) -> EventsResponse:

        async with self.session.get(
            '/api/events/',
            params={'changed_at': date},
            headers={'x-api-key': self.api_key}
        ) as response: ...

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
