from fastapi import FastAPI, Depends, HTTPException
import httpx
from datetime import datetime
from typing import List, Optional, Union, Literal
from fastapi.responses import JSONResponse
import asyncio
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session
from sqlalchemy import ForeignKey, Table, Column
from contextlib import asynccontextmanager
from sqlalchemy import text,select
from typing import Annotated
from fastapi.datastructures import State
from sqlalchemy.orm import selectinload


# Создали движок
engine = create_async_engine("sqlite+aiosqlite:///weather.db")

new_session = async_sessionmaker(engine, expire_on_commit=False)


async def get_session():
    async with new_session() as session:
        yield session

SessionDep = Annotated[AsyncSession, Depends(get_session)]

# Базовый класс для моделей
class Base(DeclarativeBase):
    pass


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


# Схема для добавления города
class CityAddSchema(BaseModel):
    user_id: int = Field(description="ID пользователя, который добавляет город")
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
    id: int = Field(description="Уникальный идентификатор города")


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


# Схема для регистрации пользователя
class UserRegSchema(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=50,
        description="Имя пользователя должно быть от 3 до 50 символов"
    )


# Схема для возврата данных о прогнозе погоды
class WeatherForecastResponse(BaseModel):
    city_id: int = Field(description="ID города")
    timestamp: datetime = Field(description="Время, когда был записан прогноз")
    temperature: Optional[float] = Field(description="Температура в градусах Цельсия")
    wind_speed: Optional[float] = Field(description="Скорость ветра в м/с")
    atmospheric_pressure: Optional[float] = Field(description="Атмосферное давление в hPa")

# Схема для принятия данных для возврата погоды в зависимости от времени
class WeatherParamsRequest(BaseModel):
    user_id: int = Field(description="ID пользователя")
    city_name: str = Field(description="Название города")
    time: str = Field(description="Время в формате 'HH:MM'")
    params: List[Literal["temperature", "humidity", "wind_speed", "precipitation"]] = Field(
        description="Список параметров погоды для возврата"
    )

# Схема для ответа с информацией о городе
class CityResponse(BaseModel):
    id: int = Field(description="Уникальный идентификатор города")
    name: str = Field(description="Название города")
    latitude: float = Field(description="Широта города")
    longitude: float = Field(description="Долгота города")
    forecast: Optional[WeatherForecastResponse] = Field(description="Прогноз погоды для города")


# схема будет использоваться для возврата данных о пользователе, включая список городов, которые он отслеживает
class UserSchema(UserRegSchema):
    id: int
    cities: List[CityResponse] = Field(description="Список городов, которые отслеживает пользователь")

# Модель Pydantic для входных данных
class UserCreateSchema(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Имя пользователя")

@app.post("/register_user", summary="Создание пользователя")
async def register_user(user: UserCreateSchema, session: SessionDep):
    """Метод создания пользователя"""

    try:
        # Проверяем, существует ли пользователь с таким именем
        existing_user = await session.execute(
            select(UserModel).where(UserModel.username == user.username)
        )
        if existing_user.scalar():
            raise HTTPException(status_code=400, detail="Username already exists")

        # Создаём нового пользователя
        new_user = UserModel(username=user.username)
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)

        return {"user_id": new_user.id}
    except Exception as err:
        await session.rollback()  # Откатываем транзакцию в случае ошибки
        raise HTTPException(status_code=500, detail=f"Unexpected error: {err}")


def find_partial_match(times, target) -> Union[int, None]:
    """Находит ближайшее совпадение по частичной дате/времени."""
    for position, time in enumerate(times):
        if time.startswith(target):  # Проверяем, начинается ли строка с целевого значения
            return position
    return None  # Если ничего не найдено


@app.get("/weather", summary="Получение текущей погоды для указанных координат")
async def get_weather(latitude: float, longitude: float):
    """Возвращает текущую погоду для указанных координат."""
    try:
        current_data_time = datetime.now().strftime(
            '%Y-%m-%dT%H')  # возвращает текущую дату без минут, например: 2025-01-13T12

        async with httpx.AsyncClient() as client:  # Создаём асинхронный запрос к Open-Meteo API
            response = await client.get("https://api.open-meteo.com/v1/forecast", params={
                "latitude": latitude,  # Передаём широту
                "longitude": longitude,  # Передаём долготу
                "current_weather": True,  # Указываем, что хотим получить значение текущей погоды
                "hourly": "pressure_msl"  # Запрашиваем атмосферное давление
            })
            if response.status_code != 200:
                return JSONResponse({'error': f'Failed to fetch weather data'}, status_code=500)

            result_data = response.json()

            try:
                index_of_the_current_date = find_partial_match(result_data["hourly"]["time"],
                                                               current_data_time)  # получаем индекс текущей даты в словаре
            except ValueError:
                return JSONResponse({'error': f'Current time not found in weather data'}, status_code=404)

            current_atmospheric_pressure_value = result_data["hourly"]["pressure_msl"][
                index_of_the_current_date]  # получаем текущее давление по индексу даты

            return {
                "temperature": result_data["current_weather"]["temperature"],
                "wind_speed": result_data["current_weather"]["windspeed"],
                "atmospheric_pressure": current_atmospheric_pressure_value
            }

    except Exception as err:
        return JSONResponse({'error': f'{err}'}, status_code=500)


@app.post("/track_city", summary="Добавление города для пользователя и сохранение текущих данных о погоде")
async def adding_city_tracking_for_user(data: CityAddSchema, session: SessionDep):
    """Метод добавляет остелижвание города для ползователя и сохраняет в бд текущий данные о погоде в этом городе"""

    try:
        # Проверяем, существует ли пользователь
        user = await session.get(UserModel, data.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")

        # Создаём город для отслеживания
        the_tracked_city_for_the_user = CityModel(
            name=data.name,
            latitude=data.latitude,
            longitude=data.longitude
        )

        # Добавляем пользователя в список отслеживающих этот город
        the_tracked_city_for_the_user.users.append(user)

        session.add(the_tracked_city_for_the_user)
        await session.commit()
        await session.refresh(the_tracked_city_for_the_user)

        # Получаем текущие данные о погоде
        current_weather_data = await get_weather(data.latitude, data.longitude)
        current_temperature = current_weather_data.get("temperature")
        current_wind_speed = current_weather_data.get("wind_speed")
        current_atmospheric_pressure = current_weather_data.get("atmospheric_pressure")

        # Проверяем, что все данные о погоде получены
        if None in (current_temperature, current_wind_speed, current_atmospheric_pressure):
            raise HTTPException(status_code=500, detail="Неполные данные о погоде")

        # Получение текущей даты и времени
        current_data_time = datetime.now()

        # Делаем запись о погоде в бд
        new_weather_record = WeatherForecastModel(city_id = the_tracked_city_for_the_user.id,timestamp = current_data_time, temperature = current_temperature,
                                               wind_speed = current_wind_speed, atmospheric_pressure = current_atmospheric_pressure)
        session.add(new_weather_record)
        session.commit()

        return JSONResponse(
            {'message': f'Added a city {data.name} for the user {data.user_id} and updated the weather forecast.'})

    except HTTPException as err:
        raise err

    except Exception as err:
        await session.rollback()  # Откатываем транзакцию в случае ошибки
        raise HTTPException(status_code=500, detail=f"Unexpected error: {err}")


async def update_weather_forecasts():
    """Обновление прогноза погоды для всех городов каждые 15 минут"""
    while True:
        try:
            # Создаем новую сессию для каждого цикла
            async with new_session() as session:
                # Получаем список всех городов
                query = select(CityModel)
                result = await session.execute(query)
                cities = result.scalars().all()

                if not cities:
                    await asyncio.sleep(15 * 60)
                    continue

                for city in cities:
                    # Получаем новый прогноз
                    current_forecast = await get_weather(city.latitude, city.longitude)
                    # Находим существующий прогноз для города
                    existing_forecast = await session.execute(
                        select(WeatherForecastModel)
                        .where(WeatherForecastModel.city_id == city.id)
                    )
                    existing_forecast = existing_forecast.scalar_one_or_none()

                    # Сохраняем прогноз в базу данных
                    current_data_time = datetime.now()

                    if existing_forecast:
                        # Обновляем существующий прогноз
                        existing_forecast.timestamp = current_data_time
                        existing_forecast.temperature = current_forecast.get("temperature")
                        existing_forecast.wind_speed = current_forecast.get("wind_speed")
                        existing_forecast.atmospheric_pressure = current_forecast.get("atmospheric_pressure")
                    else:
                        # Если прогноза нет, создаём новый
                        new_forecast = WeatherForecastModel(
                            city_id=city.id,
                            timestamp=current_data_time,
                            temperature=current_forecast.get("temperature"),
                            wind_speed=current_forecast.get("wind_speed"),
                            atmospheric_pressure=current_forecast.get("atmospheric_pressure"),
                        )
                        session.add(new_forecast)

                await session.commit()
                # Ждём 15 минут перед следующим обновлением
                print("Weather forecasts updated. Waiting for the next update...")
                await asyncio.sleep(15 * 60)

        except Exception as e:
            print(f"Error in update_weather_forecasts: {e}")
            await asyncio.sleep(15 * 60)  # Ждём перед повторной попыткой


@app.get("/list_user_cities", summary="Получение списка городов для пользователя")
async def get_cities(user_id: int, session: SessionDep ):
    """Получение списка городов для пользователя"""

    try:
        # Получаем пользователя из базы данных
        user = await session.get(UserModel, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Используем selectinload для загрузки связанных данных (города и прогнозы)
        result = await session.execute(
            select(UserModel)
            .options(selectinload(UserModel.cities).selectinload(CityModel.forecast))
            .where(UserModel.id == user_id)
        )
        user = result.scalar()

        # Получаем список городов для пользователя
        cities = user.cities

        # Преобразуем города в Pydantic-модель для ответа
        cities_response = [
            CityResponse(
                id=city.id,
                name=city.name,
                latitude=city.latitude,
                longitude=city.longitude,
                forecast=WeatherForecastResponse(
                    city_id=city.forecast.city_id,
                    timestamp=city.forecast.timestamp,
                    temperature=city.forecast.temperature,
                    wind_speed=city.forecast.wind_speed,
                    atmospheric_pressure=city.forecast.atmospheric_pressure,
                ) if city.forecast else None
            )
            for city in cities
        ]

        return {"user_id": user_id, "cities": cities_response}

    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {err}")


@app.get("/get_weather_at_time/", summary="Получение прогноза погоды для города на текущий день в указанное время")
async def get_weather_at_time(request: WeatherParamsRequest, session: SessionDep):
    """Получение прогноза погоды для города на текущий день в указанное время"""

    try:
        # Получаем пользователя из базы данных
        user = await session.get(UserModel, request.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")


        # Находим обект города по названию и проверяем, что он принадлежит пользователю
        the_city_you_are_looking_for = await session.execute(
            select(CityModel)
            .join(UserModel.cities)  # Используем связь между пользователем и городами
            .where(CityModel.name == request.city_name)
            .where(UserModel.id == request.user_id)
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
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("https://api.open-meteo.com/v1/forecast", params={
                    "latitude": latitude,
                    "longitude": longitude,
                    "current_weather": True,
                    "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation",
                    "timezone": "auto"
                })
                if response.status_code != 200:
                    return JSONResponse({"error": "Failed to fetch weather data"}, status_code=500)

                current_weather = response.json()

                # Ищем индекс времени в данных и по этому индексу находтся temperature_2m,relative_humidity_2m, wind_speed_10m
                time_index = find_partial_match(current_weather["hourly"]["time"], full_string_time)
                if time_index is None:
                    return JSONResponse({'error': 'Time not found in weather data'}, status_code=404)

                # Формируем ответ с запрошенными параметрами
                result = {}
                parameters = request.params
                if "temperature" in parameters:
                    result["temperature"] = current_weather["hourly"]["temperature_2m"][time_index]
                if "humidity" in parameters:
                    result["humidity"] = current_weather["hourly"]["relative_humidity_2m"][time_index]
                if "wind_speed" in parameters:
                    result["wind_speed"] = current_weather["hourly"]["wind_speed_10m"][time_index]
                if "precipitation" in parameters:
                    result["precipitation"] = current_weather["hourly"]["precipitation"][time_index]

                if len(result) > 0:
                    return JSONResponse(result, status_code=200)
                else:
                    return JSONResponse({"result": "No weather parameters are specified"}, status_code=200)

        except Exception as e:
            return JSONResponse({'error': str(e)}, status_code=500)
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {err}")



if __name__ == "__main__":
    import uvicorn

    uvicorn.run("script:app", host="127.0.0.1", port=8000, reload=True)
