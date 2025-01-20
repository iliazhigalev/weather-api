from typing import List
from pydantic import BaseModel, Field
from app.schemas.cities import CityResponseSchema


# Схема для регистрации пользователя
class UserRegSchema(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=50,
        description="Имя пользователя должно быть от 3 до 50 символов"
    )


# схема будет использоваться для возврата данных о пользователе, включая список городов, которые он отслеживает
class UserSchema(UserRegSchema):
    id: int
    cities: List[CityResponseSchema] = Field(default=None,
                                             description="Список городов, которые отслеживает пользователь")


# Схема возврата списка городов пользователя
class UserCitiesResponseSchema(BaseModel):
    user_id: int
    cities: List[CityResponseSchema]
