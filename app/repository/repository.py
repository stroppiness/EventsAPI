import logging
from datetime import datetime
from typing import Protocol
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import Event, Place, SyncMetadata, Ticket

logger = logging.getLogger(__name__)


class SyncRepository(Protocol):

    async def get_metadata(self) -> SyncMetadata | None: ...

    async def save_metadata(self, metadata: SyncMetadata) -> None: ...

    async def place_upsert(self, place: Place) -> None: ...

    async def event_upsert(self, event: Event) -> None: ...


class PlaceEventsRepository(Protocol):

    async def get_events(
        self,
        date_from: datetime | None,
        page: int,
        page_size: int,
    ) -> tuple[list[Event], int]: ...

    async def get_event_by_id(self, event_id: UUID) -> Event | None: ...


class TicketRepositoryProtocol(Protocol):
    """Протокол для описания контракта работы с билетами."""

    async def create_ticket(self, ticket: Ticket) -> None: ...

    async def get_ticket_by_id(self, ticket_id: UUID) -> Ticket | None: ...

    async def delete_ticket(self, ticket: Ticket) -> None: ...


class SyncEventsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_metadata(self) -> SyncMetadata | None:
        try:
            query = (
                select(SyncMetadata)
                .where(SyncMetadata.sync_status == "success")
                .order_by(desc(SyncMetadata.id))
                .limit(1)
            )

            result = await self.session.execute(query)
            return result.scalar_one_or_none()

        except SQLAlchemyError:
            logger.exception("Ошибка при получении metadata")
            raise

    async def save_metadata(self, metadata: SyncMetadata) -> None:
        try:
            self.session.add(metadata)
            await self.session.flush()

        except SQLAlchemyError:
            logger.exception("Ошибка при сохранении metadata")
            raise

    async def place_upsert(self, place: Place) -> None:
        try:
            await self.session.merge(place)
            await self.session.flush()

        except SQLAlchemyError:
            logger.exception(f"Ошибка при сохранении площадки (ID: {place.id})")
            raise

    async def event_upsert(self, event: Event) -> None:
        try:
            await self.session.merge(event)
            await self.session.flush()

        except SQLAlchemyError:
            logger.exception(f"Ошибка при сохранении события (ID: {event.id})")
            raise


class PlaceEventsRepositoryApi:
    """Репозиторий для получения событий и площадок в API."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_events(
        self,
        date_from: datetime | None,
        page: int,
        page_size: int,
    ) -> tuple[list[Event], int]:
        try:
            query = select(Event).options(selectinload(Event.place))
            count_query = select(func.count()).select_from(Event)

            if date_from is not None:
                query = query.where(Event.event_time >= date_from)
                count_query = count_query.where(Event.event_time >= date_from)

            query = (
                query.order_by(Event.event_time)
                .offset((page - 1) * page_size)
                .limit(page_size)
            )

            total_result = await self.session.execute(count_query)
            total_count = total_result.scalar_one()

            events_result = await self.session.execute(query)
            events = list(events_result.scalars().all())

            return events, total_count

        except SQLAlchemyError:
            logger.exception("Ошибка при получении списка событий")
            raise

    async def get_event_by_id(self, event_id: UUID) -> Event | None:
        try:
            query = (
                select(Event)
                .options(selectinload(Event.place))
                .where(Event.id == event_id)
            )
            result = await self.session.execute(query)
            return result.scalar_one_or_none()

        except SQLAlchemyError:
            logger.exception("Ошибка при получении события (ID: %s)", event_id)
            raise


class TicketRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_ticket(self, ticket: Ticket) -> None:
        try:
            self.session.add(ticket)
            await self.session.commit()

        except SQLAlchemyError:
            logger.exception("Ошибка при сохранении билета")
            raise

    async def get_ticket_by_id(self, ticket_id: UUID) -> Ticket | None:
        try:
            query = select(Ticket).where(Ticket.ticket_id == ticket_id)
            result = await self.session.execute(query)
            return result.scalar_one_or_none()

        except SQLAlchemyError:
            logger.exception(
                "Ошибка при получении билета (ID: %s)", ticket_id,
            )
            raise

    async def delete_ticket(self, ticket: Ticket) -> None:
        try:
            await self.session.delete(ticket)
            await self.session.commit()

        except SQLAlchemyError:
            logger.exception(
                "Ошибка при удалении билета (ID: %s)", ticket.ticket_id,
            )
            raise
