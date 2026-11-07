from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class EventRegister(BaseModel):
    first_name: str
    last_name: str
    seat: str
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)


class TicketRegisterRequest(EventRegister):
    event_id: UUID


class EventCreated(BaseModel):
    ticket_id: UUID

    model_config = ConfigDict(from_attributes=True)


class PlaceResponse(BaseModel):
    id: UUID
    name: str
    city: str
    address: str
    seats_pattern: str
    changed_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EventResponse(BaseModel):
    id: UUID
    name: str
    place: PlaceResponse
    event_time: datetime
    registration_deadline: datetime
    status: Literal['new', 'published', 'registration_closed', 'finished']
    number_of_visitors: int
    changed_at: datetime
    created_at: datetime
    status_changed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EventsResponse(BaseModel):
    next: str | None
    previous: str | None
    results: list[EventResponse]

    model_config = ConfigDict(from_attributes=True)


class PlaceApiResponse(BaseModel):
    id: UUID
    name: str
    city: str
    address: str

    model_config = ConfigDict(from_attributes=True)


class EventApiResponse(BaseModel):
    id: UUID
    name: str
    place: PlaceApiResponse
    event_time: datetime
    registration_deadline: datetime
    status: Literal['new', 'published', 'registration_closed', 'finished']
    number_of_visitors: int

    model_config = ConfigDict(from_attributes=True)


class EventsApiResponse(BaseModel):
    count: int
    next: str | None
    previous: str | None
    results: list[EventApiResponse]

    model_config = ConfigDict(from_attributes=True)


class PlaceDetailResponse(BaseModel):
    id: UUID
    name: str
    city: str
    address: str
    seats_pattern: str

    model_config = ConfigDict(from_attributes=True)


class EventDetailResponse(BaseModel):
    id: UUID
    name: str
    place: PlaceDetailResponse
    event_time: datetime
    registration_deadline: datetime
    status: Literal['new', 'published', 'registration_closed', 'finished']
    number_of_visitors: int

    model_config = ConfigDict(from_attributes=True)


class ProviderSeatsResponse(BaseModel):
    seats: list[str]

    model_config = ConfigDict(from_attributes=True)


class SeatsResponse(BaseModel):
    event_id: UUID
    available_seats: list[str]

    model_config = ConfigDict(from_attributes=True)


class UnregisterResponse(BaseModel):
    success: bool

    model_config = ConfigDict(from_attributes=True)
