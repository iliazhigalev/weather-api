from datetime import datetime
from typing import List, Optional, Union, Literal
from pydantic import BaseModel, Field


# Схема для добавления прогноза погоды
class WeatherForecastAddSchema(BaseModel):
    city_id: int = Field(description="ID города, для которого добавляется прогноз")
    temperature: Optional[float] = Field(description="Температура в градусах Цельсия")
    wind_speed: Optional[float] = Field(description="Скорость ветра в м/с")
    atmospheric_pressure: Optional[float] = Field(description="Атмосферное давление в hPa")


# Схема для возврата прогноза погоды
class WeatherForecastSchema(WeatherForecastAddSchema):
    id: int = Field(description="Уникальный идентификатор прогноза")
    timestamp: datetime = Field(description="Время, когда был записан прогноз")


# Схема для возврата данных о прогнозе погоды
class WeatherForecastResponseSchema(BaseModel):
    city_id: int = Field(description="ID города")
    timestamp: datetime = Field(description="Время, когда был записан прогноз")
    temperature: Optional[float] = Field(description="Температура в градусах Цельсия")
    wind_speed: Optional[float] = Field(description="Скорость ветра в м/с")
    atmospheric_pressure: Optional[float] = Field(description="Атмосферное давление в hPa")


# Схема для принятия данных для возврата погоды в зависимости от времени
class WeatherParamsRequestSchema(BaseModel):
    user_id: int = Field(description="ID пользователя")
    city_name: str = Field(description="Название города")
    time: str = Field(description="Время в формате 'HH:MM'")
    params: List[Literal["temperature", "humidity", "wind_speed", "precipitation"]] = Field(
        description="Список параметров погоды для возврата"
    )


# Схема для текущей погоды
class CurrentWeatherResponseSchema(BaseModel):
    temperature: float = Field(description="Температура в градусах Цельсия")
    wind_speed: float = Field(description="Скорость ветра в м/с")
    atmospheric_pressure: float = Field(description="Атмосферное давление в hPa")


# Схема для прогноза погоды на определённое время
class WeatherAtTimeResponseSchema(BaseModel):
    temperature: Optional[float] = Field(description="Температура в градусах Цельсия")
    humidity: Optional[float] = Field(description="Влажность в процентах")
    wind_speed: Optional[float] = Field(description="Скорость ветра в м/с")
    precipitation: Optional[float] = Field(description="Количество осадков в мм")
