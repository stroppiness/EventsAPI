import os
from contextlib import asynccontextmanager

import aiohttp
from dotenv import load_dotenv
from fastapi import FastAPI

from core.scheduler import API_KEY, start_scheduler, stop_scheduler
from provider_requesting.events_providers import EventsProviderHTTPClient

load_dotenv()

PROVIDER_URL = os.getenv(
    'PROVIDER_URL',
    'http://student-system-events-provider-web.'
    'student-system-events-provider.svc:8000',
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with aiohttp.ClientSession(
        base_url=PROVIDER_URL,
    ) as session:
        app.state.http_session = session

        app.state.provider_client = EventsProviderHTTPClient(
            session=session,
            api_key=API_KEY
        )

        app.state.seats_cache = {}

        start_scheduler(app)

        yield

        stop_scheduler()
