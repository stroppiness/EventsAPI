from uuid import UUID
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr


class EventRegister(BaseModel):
    first_name: str
    last_name: str
    seat: str
    email: EmailStr


class EventCreated(BaseModel):
    ticket_id: UUID


class PlaceResponse(BaseModel):
    id: UUID
    name: str
    city: str
    address: str
    seats_pattern: str
    changed_at: datetime
    created_at: datetime


class EventResponse(BaseModel):
    id: UUID
    name: str
    place: PlaceResponse


class EventsResponse(BaseModel):
    next: str | None
    previous: str | None
    results: list[EventResponse]
    event_time: datetime
    registration_deadline: datetime
    status: Literal["new", "published"]
    number_of_visitors: int
    changed_at: datetime
    created_at: datetime
    status_changed_at: datetime
