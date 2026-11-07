from contextlib import asynccontextmanager

import aiohttp
from fastapi import FastAPI

from core.config import settings
from core.scheduler import start_scheduler, stop_scheduler
from provider_requesting.events_providers import EventsProviderHTTPClient


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with aiohttp.ClientSession(
        base_url=settings.provider_url,
    ) as session:
        app.state.http_session = session

        app.state.provider_client = EventsProviderHTTPClient(
            session=session,
            api_key=settings.api_key
        )

        app.state.seats_cache = {}

        start_scheduler(app)

        yield

        stop_scheduler()
