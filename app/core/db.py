from fastapi import Depends
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from typing import Annotated
from app.models.models import Base

# Создали движок
engine = create_async_engine("sqlite+aiosqlite:///weather.db")

new_session = async_sessionmaker(engine, expire_on_commit=False)


async def get_session():
    async with new_session() as session:
        yield session


# Определяем зависимость для сессии
SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def set_up_database():
    async with engine.begin() as conn:
        # Проверяем, существует ли таблица пользователей
        result = await conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        )
        existing_tables = result.scalars().all()

        if not existing_tables:
            await conn.run_sync(Base.metadata.create_all)
            return {"message": "tables have been created"}
        else:
            return {"the tables already exist"}
