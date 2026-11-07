from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import UUID as SQLUUID
from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base


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
    place: Mapped[UUID] = mapped_column(
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

    place: Mapped['Place'] = relationship('Place', lazy='selectin')


class SyncMetadata(Base):
    __tablename__ = 'sync_metadata'
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


class Ticket(Base):
    __tablename__ = 'tickets'

    __table_args__ = (
        UniqueConstraint(
            'event_id',
            'seat',
            name='uq_ticket_event_seat',
        ),
    )

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )

    ticket_id: Mapped[UUID] = mapped_column(
        unique=True,
        nullable=False,
    )

    event_id: Mapped[UUID] = mapped_column(
        ForeignKey('events.id'),
        nullable=False,
    )

    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    seat: Mapped[str] = mapped_column(String(20), nullable=False)
