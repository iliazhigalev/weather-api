from fastapi import HTTPException
from app.core.db import SessionDep
from app.models.models import UserModel


async def get_user_by_id(user_id: int, session: SessionDep) -> UserModel:
    """
    Получает пользователя по ID. Если пользователь не найден, выбрасывает HTTPException.
    """
    user = await session.get(UserModel, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
