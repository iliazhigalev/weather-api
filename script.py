from fastapi import FastAPI, Depends, HTTPException
import asyncio
from contextlib import asynccontextmanager
from fastapi.datastructures import State
from app.core.db import set_up_database
from app.tasks import update_weather_forecasts
from app.routers import cities, weather, users

@asynccontextmanager
async def lifespan(app: FastAPI):
    await set_up_database()  # Выполняется при старте приложения

    # Указываем тип для app.state
    state: State = app.state

    # Создаем фоновую задачу и сохраняем её в app.state
    state.weather_updater = asyncio.create_task(update_weather_forecasts())

    yield

    # Отменяем задачу при завершении приложения
    state.weather_updater.cancel()
    await state.weather_updater


app = FastAPI(lifespan=lifespan)
# Подключаем роутеры
app.include_router(cities.router)
app.include_router(weather.router)
app.include_router(users.router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("script:app", host="127.0.0.1", port=8000, reload=True)
