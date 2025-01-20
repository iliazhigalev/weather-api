from fastapi import APIRouter, HTTPException
from datetime import datetime
from fastapi.responses import JSONResponse
from sqlalchemy import select
from app.services.common import find_partial_match, fetch_weather_data, fetch_weather_for_city
from app.schemas.weather import CurrentWeatherResponseSchema, WeatherParamsRequestSchema
from ..core.db import SessionDep
from ..models.models import UserModel, CityModel
from ..services.users import get_user_by_id

router = APIRouter(prefix="/weather", tags=["weather"])


@router.get("/weather", response_model=CurrentWeatherResponseSchema,
            summary="Получение текущей погоды для указанных координат")
async def get_current_weather(latitude: float, longitude: float):
    """
    Получает текущую погоду для указанных координат.
    """
    current_data_time = datetime.now().strftime('%Y-%m-%dT%H')
    weather_data = await fetch_weather_data(latitude, longitude, "pressure_msl")

    # Находим индекс текущего времени
    index_of_the_current_date = find_partial_match(weather_data["hourly"]["time"], current_data_time)
    if index_of_the_current_date is None:
        raise HTTPException(status_code=404, detail="Current time not found in weather data")

    # Получаем текущее атмосферное давление
    current_atmospheric_pressure_value = weather_data["hourly"]["pressure_msl"][index_of_the_current_date]

    return CurrentWeatherResponseSchema(
        temperature=weather_data["current_weather"]["temperature"],
        wind_speed=weather_data["current_weather"]["windspeed"],
        atmospheric_pressure=current_atmospheric_pressure_value
    )


@router.get("/get_weather_at_time/", summary="Получение прогноза погоды для города на текущий день в указанное время")
async def get_weather_at_time(request: WeatherParamsRequestSchema, session: SessionDep):
    """
    Получение прогноза погоды для города на текущий день в указанное время
    """

    # Проверяем существует ли пользователь
    user = await get_user_by_id(request.user_id, session)

    # Находим обект города по названию и проверяем, что он принадлежит пользователю
    the_city_you_are_looking_for = await session.execute(
        select(CityModel)
        .join(UserModel.cities)  # Используем связь между пользователем и городами
        .where(CityModel.name == request.city_name)
        .where(UserModel.id == user.id)
    )
    the_city_you_are_looking_for = the_city_you_are_looking_for.scalar_one_or_none()

    if not the_city_you_are_looking_for:
        raise HTTPException(status_code=404, detail="City not found or does not belong to the user")

    # Проверяем время на валидность, нам нужен только час
    the_time_you_are_looking_for = request.time[:2]
    if not the_time_you_are_looking_for.isdigit() or not (0 <= int(the_time_you_are_looking_for) < 24):
        raise HTTPException(status_code=400, detail="The entered time is incorrect")

    # Получаем дату и время по которым будет искать, например: 2025-01-14T15, где 2025-01-14-дата и 15-время
    full_string_time = datetime.now().strftime('%Y-%m-%dT') + the_time_you_are_looking_for

    latitude, longitude = the_city_you_are_looking_for.latitude, the_city_you_are_looking_for.longitude
    # Получаем данные о погоде
    weather_result = await fetch_weather_for_city(latitude, longitude, full_string_time, request.params)

    if not weather_result:
        return JSONResponse({"result": "No weather parameters are specified"}, status_code=200)

    return JSONResponse(weather_result, status_code=200)
