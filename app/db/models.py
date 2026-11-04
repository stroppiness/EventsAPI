from datetime import datetime
from uuid import UUID, uuid4

from db.database import Base
from sqlalchemy import UUID as SQLUUID
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column


class Place(Base):
    __tablename__ = 'places'

    id: Mapped[UUID] = mapped_column(
        SQLUUID(as_uuid=True),
        primary_key=True,
    )
    name: Mapped[str] = mapped_column()
    city: Mapped[str] = mapped_column()
    address: Mapped[str] = mapped_column()
    seats_pattern: Mapped[str] = mapped_column()
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
    )


class Event(Base):
    __tablename__ = 'events'

    id: Mapped[UUID] = mapped_column(
        SQLUUID(as_uuid=True),
        primary_key=True,
    )
    name: Mapped[str] = mapped_column()
    place_id: Mapped[UUID] = mapped_column(
        SQLUUID(as_uuid=True),
        ForeignKey('places.id'),

    )
    event_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
    )
    registration_deadline: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
    )
    status: Mapped[str] = mapped_column()
    number_of_visitors: Mapped[int] = mapped_column()
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
    )
    status_changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
    )


class SyncMetadata(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    last_sync_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    sync_status: Mapped[str] = mapped_column(String(20))
