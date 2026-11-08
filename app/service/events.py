import time as time_module
from datetime import UTC, date, datetime, time, timedelta, timezone
from uuid import UUID

from db.models import Event, Place, Ticket
from provider_requesting.events_providers import (
    EventsPaginator,
    EventsProviderClient,
    EventsProviderHTTPClient,
)
from provider_requesting.exceptions import (
    EventNotFoundError,
    EventNotPublishedError,
    RegistrationDeadlinePassedError,
    SeatNotAvailableError,
)
from provider_requesting.schemas import (
    EventCreated,
    EventDetailResponse,
    EventRegister,
    SeatsResponse,
    UnregisterResponse,
)
from repository.repository import (
    PlaceEventsRepository,
    PlaceEventsRepositoryApi,
    SyncRepository,
    TicketRepository,
)
from service.exceptions import TicketNotFoundError

UTC_PLUS_3 = timezone(timedelta(hours=3))


class EventSyncClientService:

    def __init__(
        self,
        provider_client: EventsProviderClient,
        sync_repository: SyncRepository,
    ):
        self.provider_client = provider_client
        self.sync_repository = sync_repository

    async def sync_events(self) -> None:
        metadata = await self.sync_repository.get_metadata()

        if metadata is None:
            changed_at = datetime(2000, 1, 1, tzinfo=UTC)
        else:
            changed_at = metadata.last_changed_at

        paginator = EventsPaginator(
            client=self.provider_client,
            changed_at=changed_at,
        )
        async for event in paginator:
            place = event.place
            place_data = place.model_dump()
            db_place = Place(**place_data)
            await self.sync_repository.place_upsert(db_place)

            event_data = event.model_dump()
            event_data.pop("place")
            event_data["place_id"] = event.place.id
            db_event = Event(**event_data)
            await self.sync_repository.event_upsert(db_event)


class PlaceEventsService:
    def __init__(self, repository: PlaceEventsRepositoryApi):
        self.repository = repository

    async def get_events(
        self,
        date_from: date | None,
        page: int,
        page_size: int,
    ) -> tuple[list[Event], int]:

        date_from_datetime = None

        if date_from is not None:
            date_from_datetime = datetime.combine(
                date_from,
                time.min,
                tzinfo=UTC_PLUS_3,
            )

        events, count = await self.repository.get_events(
            date_from=date_from_datetime,
            page=page,
            page_size=page_size,
        )

        return events, count

    async def get_event_by_id(
        self,
        event_id: UUID,
    ) -> EventDetailResponse | None:

        event = await self.repository.get_event_by_id(event_id)

        if event is None:
            return None

        event_data = {
            "id": event.id,
            "name": event.name,
            "place": {
                "id": event.place.id,
                "name": event.place.name,
                "city": event.place.city,
                "address": event.place.address,
                "seats_pattern": event.place.seats_pattern,
            },
            "event_time": event.event_time,
            "registration_deadline": event.registration_deadline,
            "status": event.status,
            "number_of_visitors": event.number_of_visitors,
        }

        return EventDetailResponse(**event_data)


class SeatsService:
    CACHE_TTL = 30

    def __init__(
        self,
        repository: PlaceEventsRepositoryApi,
        provider_client: EventsProviderHTTPClient,
        cache: dict,
    ):
        self.repository = repository
        self.provider_client = provider_client
        self.cache = cache

    async def get_available_seats(
        self,
        event_id: UUID,
    ) -> SeatsResponse | None:

        event = await self.repository.get_event_by_id(event_id)

        if event is None:
            return None

        if event.status != 'published':
            raise EventNotPublishedError('Event is not published')

        cached_data = self.cache.get(event_id)

        if cached_data is not None:
            cached_at, seats = cached_data

            if time_module.monotonic() - cached_at < self.CACHE_TTL:
                return SeatsResponse(
                    event_id=event_id,
                    available_seats=seats,
                )

        provider_response = await self.provider_client.get_available_seats(
            event_id,
        )

        seats = provider_response.seats

        self.cache[event_id] = (time_module.monotonic(), seats)

        return SeatsResponse(
            event_id=event_id,
            available_seats=seats,
        )


class TicketService:

    def __init__(
        self,
        ticket_repository: TicketRepository,
        event_repository: PlaceEventsRepository,
        provider_client: EventsProviderClient,
        seats_service: SeatsService,
    ):
        self.ticket_repository = ticket_repository
        self.event_repository = event_repository
        self.provider_client = provider_client
        self.seats_service = seats_service

    async def register(self, data: EventRegister) -> EventCreated:
        event = await self.event_repository.get_event_by_id(data.event_id)

        if event is None:
            raise EventNotFoundError("Мероприятие не найдено")
        if event.status != "published":
            raise EventNotPublishedError(
                "Регистрация на мероприятие недоступна"
            )

        if datetime.now(UTC) >= event.registration_deadline:
            raise RegistrationDeadlinePassedError(
                "Срок регистрации истёк"
            )

        seats_response = await self.seats_service.get_available_seats(
            data.event_id
        )

        if data.seat not in seats_response.available_seats:
            raise SeatNotAvailableError("Выбранное место недоступно")

        provider_data = EventRegister(
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,
            seat=data.seat,
        )

        provider_response = await self.provider_client.register(
            data.event_id,
            provider_data,
        )

        ticket = Ticket(
            ticket_id=provider_response.ticket_id,
            event_id=data.event_id,
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,
            seat=data.seat,
        )

        await self.ticket_repository.create_ticket(ticket)

        return provider_response

    async def unregister(self, ticket_id: UUID) -> UnregisterResponse:
        ticket = await self.ticket_repository.get_ticket_by_id(ticket_id)

        if ticket is None:
            raise TicketNotFoundError("Билет не найден")

        provider_response = await self.provider_client.unregister(
            event_id=ticket.event_id,
            ticket_id=ticket.ticket_id,
        )

        if provider_response.success:
            await self.ticket_repository.delete_ticket(ticket)

        return provider_response
