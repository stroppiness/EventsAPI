import asyncio
import logging
import os
from datetime import UTC, datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

from db.database import SessionLocal
from db.models import SyncMetadata
from provider_requesting.events_providers import EventsProviderHTTPClient
from repository.repository import SyncEventsRepository
from service.events import EventSyncClientService

load_dotenv()

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()
sync_lock = asyncio.Lock()

API_KEY = os.getenv('API_KEY')


async def run_sync(app):
    if sync_lock.locked():
        logger.warning("Синхронизация уже выполняется, пропускаем запуск")
        return

    async with sync_lock:
        sync_started_at = datetime.now(UTC)

        try:
            async with SessionLocal() as session:
                repository = SyncEventsRepository(session)

                provider_client = EventsProviderHTTPClient(
                    session=app.state.http_session,
                    api_key=API_KEY,
                )

                sync_service = EventSyncClientService(
                    provider_client=provider_client,
                    sync_repository=repository,
                )

                async with session.begin():
                    await sync_service.sync_events()

                    metadata = SyncMetadata(
                        sync_status="success",
                        last_sync_time=datetime.now(UTC),
                        last_changed_at=sync_started_at,
                    )
                    await repository.save_metadata(metadata)

        except Exception:
            logger.exception("Ошибка фоновой синхронизации")

            try:
                async with SessionLocal() as session:
                    repository = SyncEventsRepository(session)

                    async with session.begin():
                        metadata = SyncMetadata(
                            sync_status="failed",
                            last_sync_time=sync_started_at,
                            last_changed_at=None,
                        )
                        await repository.save_metadata(metadata)

            except Exception:
                logger.exception("Не удалось сохранить статус failed")

            raise


def start_scheduler(app):
    scheduler.add_job(
        run_sync,
        max_instances=1,
        coalesce=True,
        trigger=CronTrigger(hour=3, minute=0),
        args=[app],
        id="events_sync",
        replace_existing=True,
    )

    scheduler.start()


def stop_scheduler():
    scheduler.shutdown()
