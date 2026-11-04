from app.api.fromfastapi import FastAPI
from app.core.lifespan import lifespan

app = FastAPI(lifespan=lifespan)

app.include_router(api_router)