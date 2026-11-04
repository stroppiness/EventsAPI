from datetime import date, datetime, time, timedelta, timezone
from typing import Protocol
from uuid import UUID

from db.models import Event, Place, SyncMetadata
from provider_requesting.events_providers import EventsProviderClient
from provider_requesting.schemas import EventDetailResponse
from repository.repository import (EventRepository, PlaceEventsRepositoryApi,
                                   PlaceRepository, SyncRepository)

UTC_PLUS_3 = timezone(timedelta(hours=3))

class EventSyncClient(Protocol):

    async def sync_events(self) -> None: ...


class PlaceEvents(Protocol):

    async def get_events(
        self,
        date_from: date | None,
        page: int,
        page_size: int,
    ) -> tuple[list[Event], int]: ...


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
            changed_at = datetime(2000, 1, 1, tzinfo=timezone.utc)
        else:
            changed_at = metadata.last_changed_at

        events = await self.provider_client.get_all_events(changed_at)

        for event in events:
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
