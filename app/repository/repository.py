import logging
from datetime import datetime
from typing import Protocol
from uuid import UUID

from db.models import Event, Place, SyncMetadata
from sqlalchemy import desc, func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


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


logger = logging.getLogger(__name__)

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
