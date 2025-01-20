from datetime import datetime
from typing import List, Optional, Union, Literal
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session
from sqlalchemy import ForeignKey, Table, Column


# Базовый класс для моделей
class Base(DeclarativeBase):
    pass


# Таблица для связи многие-ко-многим между пользователями и городами
user_city_association = Table(
    "user_city_association",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("city_id", ForeignKey("cities.id"), primary_key=True),
)


# Модель для пользователей
class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(unique=True, nullable=False)

    # Связь с городами. Список городов, которые отслеживает пользователь.
    cities: Mapped[List["CityModel"]] = relationship(
        "CityModel", secondary=user_city_association, back_populates="users"
    )


# Модель для городов
class CityModel(Base):
    __tablename__ = "cities"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(nullable=False)
    latitude: Mapped[float] = mapped_column(nullable=False)
    longitude: Mapped[float] = mapped_column(nullable=False)

    # Связь с пользователями. Список пользователей, которые отслеживают этот город.
    users: Mapped[List["UserModel"]] = relationship(
        "UserModel", secondary=user_city_association, back_populates="cities"
    )

    # Прогнозпогоды города
    forecast: Mapped["WeatherForecastModel"] = relationship(
        "WeatherForecastModel", back_populates="city", uselist=False
    )


# Модель для прогнозов погоды.
class WeatherForecastModel(Base):
    __tablename__ = "weather_forecasts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    city_id: Mapped[int] = mapped_column(ForeignKey("cities.id"), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(nullable=False)
    temperature: Mapped[float] = mapped_column(nullable=True)
    wind_speed: Mapped[float] = mapped_column(nullable=True)
    atmospheric_pressure: Mapped[float] = mapped_column(nullable=True)

    # Связь с городом. У одного города один прогноз погоды.
    city: Mapped["CityModel"] = relationship("CityModel", back_populates="forecast")
