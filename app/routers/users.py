from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text, select
from app.core.db import SessionDep
from app.models.models import UserModel
from app.schemas.users import UserSchema, UserRegSchema
from sqlalchemy.exc import IntegrityError

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register_user", response_model=UserSchema)
async def register_user(user: UserRegSchema, session: SessionDep):
    """
    Метод регистриции (создания) пользователя.
    """
    # Проверяем, существует ли пользователь с таким именем
    existing_user = await session.execute(
        select(UserModel).where(UserModel.username == user.username)
    )
    if existing_user.scalar():
        raise HTTPException(status_code=400, detail="Username already exists")

    # Создаём нового пользователя
    new_user = UserModel(username=user.username)
    session.add(new_user)

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Username already exists")
    except Exception as err:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Unexpected error: {err}")

    await session.refresh(new_user)

    return UserSchema(
        id=new_user.id,
        username=new_user.username
    )
