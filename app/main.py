from app.api. from fastapi import FastAPI
from app.core.lifespan import lifespan

app = FastAPI(lifespan=lifespan)

app.include_router(api_router)