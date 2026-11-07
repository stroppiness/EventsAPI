import asyncio

from sqlalchemy import text

from db.database import engine


async def main():
    async with engine.begin() as conn:
        await conn.execute(text(
            'DROP TABLE IF EXISTS tickets, events, places, '
            'sync_metadata, alembic_version CASCADE'
        ))
    await engine.dispose()
    print('reset_db: tables dropped', flush=True)


asyncio.run(main())
