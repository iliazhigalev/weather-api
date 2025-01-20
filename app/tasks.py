from datetime import datetime
import asyncio
from sqlalchemy import select
from app.core.db import new_session
from app.models.models import CityModel, WeatherForecastModel
from app.routers.weather import get_current_weather

async def update_weather_forecasts():
    """
    Фоновая задача для обновления прогнозов погоды для всех городов каждые 15 минут.
    """
    while True:
        async with new_session() as session:
            try:
                # Получаем список всех городов
                query = select(CityModel)
                result = await session.execute(query)
                cities = result.scalars().all()

                if not cities:
                    print("No cities found. Waiting for the next update...")
                    await asyncio.sleep(15 * 60)
                    continue

                # Обновляем прогнозы для каждого города
                for city in cities:
                    try:
                        # Получаем текущий прогноз погоды
                        current_forecast = await get_current_weather(city.latitude, city.longitude)
                        current_data_time = datetime.now()

                        # Находим существующий прогноз для города
                        existing_forecast = await session.execute(
                            select(WeatherForecastModel)
                            .where(WeatherForecastModel.city_id == city.id)
                        )
                        existing_forecast = existing_forecast.scalar_one_or_none()

                        if existing_forecast:
                            # Обновляем существующий прогноз
                            existing_forecast.timestamp = current_data_time
                            existing_forecast.temperature = current_forecast.temperature
                            existing_forecast.wind_speed = current_forecast.wind_speed
                            existing_forecast.atmospheric_pressure = current_forecast.atmospheric_pressure
                        else:
                            # Создаём новый прогноз, если он отсутствует
                            new_forecast = WeatherForecastModel(
                                city_id=city.id,
                                timestamp=current_data_time,
                                temperature=current_forecast.temperature,
                                wind_speed=current_forecast.wind_speed,
                                atmospheric_pressure=current_forecast.atmospheric_pressure,
                            )
                            session.add(new_forecast)

                    except Exception as e:
                        print(f"Error updating forecast for city {city.name}: {e}")
                        continue  # Продолжаем обновление для других городов

                # Сохраняем изменения в базе данных
                await session.commit()
                print("Weather forecasts updated. Waiting for the next update...")

            except Exception as e:
                print(f"Error in update_weather_forecasts: {e}")
                await session.rollback()  # Откатываем транзакцию в случае ошибки

            # Ждём 15 минут перед следующим обновлением
            await asyncio.sleep(15 * 60)