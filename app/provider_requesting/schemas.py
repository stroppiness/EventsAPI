from datetime import datetime
from typing import Literal
from uuid import UUID

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
    event_time: datetime
    registration_deadline: datetime
    status: Literal["new", "published"]
    number_of_visitors: int
    changed_at: datetime
    created_at: datetime
    status_changed_at: datetime


class EventsResponse(BaseModel):
    next: str | None
    previous: str | None
    results: list[EventResponse]


class PlaceApiResponse(BaseModel):
    id: UUID
    name: str
    city: str
    address: str


class EventApiResponse(BaseModel):
    id: UUID
    name: str
    place: PlaceApiResponse
    event_time: datetime
    registration_deadline: datetime
    status: Literal["new", "published"]
    number_of_visitors: int

class EventsApiResponse(BaseModel):
    count: int
    next: str | None
    previous: str | None
    results: list[EventApiResponse]


class PlaceDetailResponse(BaseModel):
    id: UUID
    name: str
    city: str
    address: str
    seats_pattern: str


class EventDetailResponse(BaseModel):
    id: UUID
    name: str
    place: PlaceDetailResponse
    event_time: datetime
    registration_deadline: datetime
    status: str
    number_of_visitors: int


class ProviderSeatsResponse(BaseModel):
    seats: list[str]


class SeatsResponse(BaseModel):
    event_id: UUID
    available_seats: list[str]


class UnregisterResponse(BaseModel):
    success: bool
