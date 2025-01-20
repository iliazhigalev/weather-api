import sys
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.db import SessionDep
from app.models.models import UserModel

# Добавляем корневую папку проекта в sys.path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

print("----", project_root)  # Проверяем, что путь правильный

# Теперь можно импортировать script.py
from script import app

client = TestClient(app)


@pytest.fixture(autouse=True)
async def delete_test_user():
    """
    Фикстура для удаления пользователя testuser перед каждым тестом, если он существует.
    """
    async with SessionDep() as session:
        # Ищем пользователя с именем testuser
        result = await session.execute(select(UserModel).where(UserModel.username == "testuser"))
        user = result.scalar_one_or_none()

        # Если пользователь существует, удаляем его
        if user:
            await session.delete(user)
            await session.commit()


def test_register_user():
    """
    Тест для регистрации пользователя.
    """
    response = client.post(
        "/users/register_user",
        json={"username": "testuser"}  # Используем фиксированное имя пользователя
    )
    assert response.status_code == 200
    assert response.json() == {"id": 1, "username": "testuser", "cities": None}


def test_register_user_duplicate():
    """
    Тест для проверки регистрации пользователя с уже существующим именем.
    """
    # Регистрируем пользователя в первый раз
    client.post("/users/register_user", json={"username": "testuser"})

    # Пытаемся зарегистрировать пользователя с тем же именем
    response = client.post(
        "/users/register_user",
        json={"username": "testuser"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Username already exists"}

# тесты запускаются с помощью pytest app/tests/
