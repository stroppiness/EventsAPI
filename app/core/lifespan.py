from contextlib import asynccontextmanager

import aiohttp
from fastapi import FastAPI

from core.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with aiohttp.ClientSession(
        base_url='http://events-provider.dev-2.python-labs.ru',
    ) as session:
        app.state.http_session = session

        start_scheduler(app)

        yield

        stop_scheduler()
