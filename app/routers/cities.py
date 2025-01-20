from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from datetime import datetime
from ..core.db import SessionDep
from ..models.models import UserModel, CityModel, WeatherForecastModel
from ..schemas.cities import CityAddSchema, CityResponseSchema
from ..schemas.users import UserCitiesResponseSchema
from ..schemas.weather import WeatherForecastResponseSchema
from app.routers.weather import get_current_weather
from ..services.users import get_user_by_id

router = APIRouter(prefix="/cities", tags=["cities"])


@router.post("/track_city", response_model=CityResponseSchema,
             summary="Добавление города для пользователя и сохранение текущих данных о погоде")
async def adding_city_tracking_for_user(data: CityAddSchema, session: SessionDep):
    """
       Добавляет город для отслеживания пользователем и сохраняет текущие данные о погоде.
    """
    # Получаем пользователя
    user = await get_user_by_id(data.user_id, session)

    # Создаём город для отслеживания
    the_tracked_city_for_the_user = CityModel(
        name=data.name,
        latitude=data.latitude,
        longitude=data.longitude
    )

    # Добавляем пользователя в список отслеживающих этот город
    the_tracked_city_for_the_user.users.append(user)
    session.add(the_tracked_city_for_the_user)

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Город уже существует или данные некорректны")

    await session.refresh(the_tracked_city_for_the_user)

    # Получаем текущие данные о погоде
    current_weather_data = await get_current_weather(data.latitude, data.longitude)
    current_temperature = current_weather_data.temperature
    current_wind_speed = current_weather_data.wind_speed
    current_atmospheric_pressure = current_weather_data.atmospheric_pressure

    # Проверяем, что все данные о погоде получены
    if None in (current_temperature, current_wind_speed, current_atmospheric_pressure):
        raise HTTPException(status_code=500, detail="Неполные данные о погоде")

    # Получение текущей даты и времени
    current_data_time = datetime.now()

    # Делаем запись о погоде в бд
    new_weather_record = WeatherForecastModel(city_id=the_tracked_city_for_the_user.id, timestamp=current_data_time,
                                              temperature=current_temperature,
                                              wind_speed=current_wind_speed,
                                              atmospheric_pressure=current_atmospheric_pressure)
    session.add(new_weather_record)
    try:
        await session.commit()
    except Exception as err:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при сохранении данных о погоде: {err}")

    return CityResponseSchema(
        id=the_tracked_city_for_the_user.id,
        name=the_tracked_city_for_the_user.name,
        latitude=the_tracked_city_for_the_user.latitude,
        longitude=the_tracked_city_for_the_user.longitude,
        forecast=WeatherForecastResponseSchema(
            city_id=new_weather_record.city_id,
            timestamp=new_weather_record.timestamp,
            temperature=new_weather_record.temperature,
            wind_speed=new_weather_record.wind_speed,
            atmospheric_pressure=new_weather_record.atmospheric_pressure,
        )
    )


@router.get("/list_user_cities", response_model=UserCitiesResponseSchema,
            summary="Получение списка городов для пользователя")
async def list_user_cities(user_id: int, session: SessionDep):
    """
    Возвращает список городов, которые отслеживает пользователь.
    """
    # Проверяем существует ли пользователь
    user = await get_user_by_id(user_id, session)

    # Используем selectinload для загрузки связанных данных (города и прогнозы)
    result = await session.execute(
        select(UserModel)
        .options(selectinload(UserModel.cities).selectinload(CityModel.forecast))
        .where(UserModel.id == user.id)
    )
    user = result.scalar()

    # Получаем список городов для пользователя
    cities = user.cities

    # Преобразуем города в Pydantic-модель для ответа
    cities_response = [
        CityResponseSchema(
            id=city.id,
            name=city.name,
            latitude=city.latitude,
            longitude=city.longitude,
            forecast=WeatherForecastResponseSchema(
                city_id=city.forecast.city_id,
                timestamp=city.forecast.timestamp,
                temperature=city.forecast.temperature,
                wind_speed=city.forecast.wind_speed,
                atmospheric_pressure=city.forecast.atmospheric_pressure,
            ) if city.forecast else None
        )
        for city in cities
    ]

    # Возвращаем ответ с user_id и списком городов
    return UserCitiesResponseSchema(
        user_id=user.id,
        cities=cities_response
    )
