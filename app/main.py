from api.events import router as event_router
from core.lifespan import lifespan
from fastapi import FastAPI

app = FastAPI(lifespan=lifespan)

app.include_router(event_router, prefix='/api', tags=['Event'])
