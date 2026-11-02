import aiohttp

from contextlib import asynccontextmanager

from app.main import app
from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with aiohttp.ClientSession(
        base_url='http://events-provider.dev-2.python-labs.ru',
    ) as session:
        app.state.http_session = session
        yield
