from typing import List, Optional, Union, Literal
from pydantic import BaseModel, Field

from app.schemas.weather import WeatherForecastResponseSchema


# Схема для добавления города
class CityAddSchema(BaseModel):
    user_id: int = Field(
        description="ID пользователя, который добавляет город"
    )
    name: str = Field(
        min_length=2,
        max_length=20,
        description="Название города должно быть от 2 до 20 символов"
    )
    latitude: float = Field(
        ge=-90,
        le=90,
        description="Широта должна быть в диапазоне от -90 до +90"
    )
    longitude: float = Field(
        ge=-180,
        le=180,
        description="Долгота должна быть в диапазоне от -180 до +180"
    )


# Схема для возврата города
class CitySchema(CityAddSchema):
    id: int = Field(
        description="Уникальный идентификатор города"
    )


# Схема для ответа с информацией о городе
class CityResponseSchema(BaseModel):
    id: int = Field(description="Уникальный идентификатор города")
    name: str = Field(description="Название города")
    latitude: float = Field(description="Широта города")
    longitude: float = Field(description="Долгота города")
    forecast: Optional[WeatherForecastResponseSchema] = Field(description="Прогноз погоды для города")
