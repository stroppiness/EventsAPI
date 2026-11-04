from datetime import date
from uuid import UUID

from db.database import SessionDep
from fastapi import APIRouter, HTTPException, Query, Request, status
from provider_requesting.schemas import (EventDetailResponse,
                                         EventsApiResponse, SeatsResponse)
from repository.repository import PlaceEventsRepositoryApi
from scheduler import run_sync
from service.events import (EventSyncClientService, PlaceEventsService,
                            SeatsService)

router = APIRouter()


@router.get('/health', status_code=status.HTTP_200_OK)
async def healthcheck():
    """Проверка статуса работы приложения."""
    return {'status': 'ok'}


@router.post('/sync/trigger', status_code=status.HTTP_200_OK)
async def trigger_sync(request: Request):
    """Ручной запуск синхронизации."""
    await run_sync(request.app)

    return {"detail": "Синхронизация успешно завершена"}


@router.get(
    '/api/events',
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
    "/api/events/{event_id}",
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
            detail="Event not found",
        )

    return event


@router.get(
    "/api/events/{event_id}/seats",
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

    service = SeatsService(
        repository=repository,
        provider_client=provider_client,
    )

    try:
        result = await service.get_available_seats(event_id)

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Event is not published",
        )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    return result
