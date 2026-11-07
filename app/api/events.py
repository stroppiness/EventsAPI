import asyncio
from datetime import date
from uuid import UUID

from core.scheduler import run_sync, sync_lock
from fastapi import APIRouter, HTTPException, Query, Request, status

from db.database import SessionDep
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
    EventsApiResponse,
    SeatsResponse,
    UnregisterResponse,
)
from repository.repository import PlaceEventsRepositoryApi, TicketRepository
from service.events import PlaceEventsService, SeatsService, TicketService
from service.exceptions import TicketNotFoundError

router = APIRouter()


async def _run_sync_safe(app) -> None:
    try:
        await run_sync(app)
    except Exception:
        pass


@router.get('/health', status_code=status.HTTP_200_OK)
async def healthcheck():
    """Проверка статуса работы приложения."""
    return {'status': 'ok'}


@router.post('/sync/trigger', status_code=status.HTTP_202_ACCEPTED)
async def trigger_sync(request: Request):
    """Ручной запуск синхронизации в фоне."""
    if sync_lock.locked():
        return {'detail': 'Синхронизация уже выполняется'}

    request.app.state.sync_task = asyncio.create_task(
        _run_sync_safe(request.app)
    )
    return {'detail': 'Синхронизация запущена'}


@router.get(
    '/events',
    status_code=status.HTTP_200_OK,
    response_model=EventsApiResponse,
)
async def get_events(
    db: SessionDep,
    request: Request,
    date_from: date | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    repository = PlaceEventsRepositoryApi(db)
    service = PlaceEventsService(repository)

    events, count = await service.get_events(
        date_from=date_from,
        page=page,
        page_size=page_size,
    )

    next_url = None
    previous_url = None

    if page * page_size < count:
        next_url = str(
            request.url.include_query_params(page=page + 1),
        )

    if page > 1:
        previous_url = str(
            request.url.include_query_params(page=page - 1),
        )

    return EventsApiResponse(
        count=count,
        next=next_url,
        previous=previous_url,
        results=events,
    )


@router.get(
    "/events/{event_id}",
    status_code=status.HTTP_200_OK,
    response_model=EventDetailResponse,
)
async def get_event(
    event_id: UUID,
    db: SessionDep,
):
    repository = PlaceEventsRepositoryApi(db)
    service = PlaceEventsService(repository)

    event = await service.get_event_by_id(event_id)

    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Событие не найдено",
        )

    return event


@router.get(
    "/events/{event_id}/seats",
    status_code=status.HTTP_200_OK,
    response_model=SeatsResponse,
)
async def get_available_seats(
    event_id: UUID,
    db: SessionDep,
    request: Request,
):
    repository = PlaceEventsRepositoryApi(db)

    provider_client = request.app.state.provider_client

    cache = request.app.state.seats_cache

    service = SeatsService(
        repository=repository,
        provider_client=provider_client,
        cache=cache,
    )

    try:
        result = await service.get_available_seats(event_id)

    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Event is not published",
        ) from err

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    return result


@router.post(
    "/tickets",
    status_code=status.HTTP_201_CREATED,
    response_model=EventCreated,
)
async def register_ticket(
    data: EventRegister,
    db: SessionDep,
    request: Request,
):
    ticket_repository = TicketRepository(db)
    repository = PlaceEventsRepositoryApi(db)

    provider_client = request.app.state.provider_client

    seats_service = SeatsService(
        repository=repository,
        provider_client=provider_client,
        cache=request.app.state.seats_cache,
    )

    service = TicketService(
        ticket_repository=ticket_repository,
        event_repository=repository,
        provider_client=provider_client,
        seats_service=seats_service,
    )

    try:
        return await service.register(data)

    except EventNotFoundError as err:
        raise HTTPException(404, detail="Event not found") from err

    except EventNotPublishedError as err:
        raise HTTPException(
            400,
            detail="Event is not published") from err

    except RegistrationDeadlinePassedError as err:
        raise HTTPException(
            400,
            detail="Registration deadline has passed") from err

    except SeatNotAvailableError as err:
        raise HTTPException(400, detail="Seat is not available") from err


@router.delete(
    "/tickets/{ticket_id}",
    response_model=UnregisterResponse,
    status_code=status.HTTP_200_OK,
)
async def unregister_ticket(
    ticket_id: UUID,
    db: SessionDep,
    request: Request,
):
    ticket_repository = TicketRepository(db)
    repository = PlaceEventsRepositoryApi(db)

    provider_client = request.app.state.provider_client

    seats_service = SeatsService(
        repository=repository,
        provider_client=provider_client,
        cache=request.app.state.seats_cache,
    )

    service = TicketService(
        ticket_repository=ticket_repository,
        event_repository=repository,
        provider_client=provider_client,
        seats_service=seats_service,
    )

    try:
        return await service.unregister(ticket_id)

    except TicketNotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        ) from err
