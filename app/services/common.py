from fastapi import FastAPI, Depends, HTTPException
import httpx
from datetime import datetime
from typing import List, Optional, Union, Literal

from app.core.db import SessionDep
from app.models.models import UserModel


def find_partial_match(times, target) -> Union[int, None]:
    """Находит ближайшее совпадение по частичной дате/времени."""
    for position, time in enumerate(times):
        if time.startswith(target):  # Проверяем, начинается ли строка с целевого значения
            return position
    return None  # Если ничего не найдено


async def fetch_weather_data(latitude: float, longitude: float, hourly_params: str):
    """
    Выполняет запрос к API погоды и возвращает данные.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.open-meteo.com/v1/forecast", params={
            "latitude": latitude,
            "longitude": longitude,
            "current_weather": True,
            "hourly": hourly_params,
            "timezone": "auto"
        })
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to fetch weather data")
        return response.json()


async def fetch_weather_for_city(latitude: float, longitude: float, target_time: str, params: list) -> dict:
    """
    Получает данные о погоде для указанных координат и времени.
    Возвращает словарь с запрошенными параметрами.
    """
    weather_data = await fetch_weather_data(latitude, longitude, "temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation")
    time_index = find_partial_match(weather_data["hourly"]["time"], target_time)
    if time_index is None:
        raise HTTPException(status_code=404, detail="Time not found in weather data")

    result = {}
    if "temperature" in params:
        result["temperature"] = weather_data["hourly"]["temperature_2m"][time_index]
    if "humidity" in params:
        result["humidity"] = weather_data["hourly"]["relative_humidity_2m"][time_index]
    if "wind_speed" in params:
        result["wind_speed"] = weather_data["hourly"]["wind_speed_10m"][time_index]
    if "precipitation" in params:
        result["precipitation"] = weather_data["hourly"]["precipitation"][time_index]

    return result
