from fastapi import APIRouter, HTTPException, status

from db.database import SessionDep

router = APIRouter


@router.get('/health', status_code=status.HTTP_200_OK)
async def healthcheck(db: SessionDep):
    """Проверка статуса работы приложения."""
    return {'status': 'ok'}


@router.post('/sync/trigger', status_code=status.HTTP_200_OK)
async def ds():
    """Ручной запуск синхронизации."""
    pass
