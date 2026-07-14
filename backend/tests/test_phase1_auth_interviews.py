import asyncio
from collections.abc import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db_session
from app.main import app


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def setup_database() -> None:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    async def teardown_database() -> None:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.drop_all)
        await engine.dispose()

    async def override_get_db_session() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    asyncio.run(setup_database())
    app.dependency_overrides[get_db_session] = override_get_db_session

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    asyncio.run(teardown_database())


def register_user(
    client: TestClient,
    username: str = "demo_user",
    email: str = "demo@example.com",
    password: str = "Password123",
) -> dict[str, object]:
    response = client.post(
        "/api/v1/auth/register",
        json={"username": username, "email": email, "password": password},
    )
    assert response.status_code == 201
    return response.json()


def login_user(
    client: TestClient,
    username_or_email: str = "demo_user",
    password: str = "Password123",
) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"username_or_email": username_or_email, "password": password},
    )
    assert response.status_code == 200
    return str(response.json()["access_token"])


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_register_success(client: TestClient) -> None:
    data = register_user(client)

    assert data["username"] == "demo_user"
    assert data["email"] == "demo@example.com"
    assert "password_hash" not in data


def test_duplicate_username_or_email_register_fails(client: TestClient) -> None:
    register_user(client)

    duplicate_username = client.post(
        "/api/v1/auth/register",
        json={
            "username": "demo_user",
            "email": "another@example.com",
            "password": "Password123",
        },
    )
    duplicate_email = client.post(
        "/api/v1/auth/register",
        json={
            "username": "another_user",
            "email": "demo@example.com",
            "password": "Password123",
        },
    )

    assert duplicate_username.status_code == 409
    assert duplicate_email.status_code == 409


def test_login_success(client: TestClient) -> None:
    register_user(client)

    token = login_user(client, username_or_email="demo@example.com")

    assert token


def test_login_wrong_password_fails(client: TestClient) -> None:
    register_user(client)

    response = client.post(
        "/api/v1/auth/login",
        json={"username_or_email": "demo_user", "password": "WrongPassword123"},
    )

    assert response.status_code == 401


def test_me_without_token_returns_401(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401


def test_me_with_token_success(client: TestClient) -> None:
    register_user(client)
    token = login_user(client)

    response = client.get("/api/v1/auth/me", headers=auth_headers(token))

    assert response.status_code == 200
    assert response.json()["username"] == "demo_user"


def test_create_interview_after_login_success(client: TestClient) -> None:
    register_user(client)
    token = login_user(client)

    response = client.post(
        "/api/v1/interviews",
        headers=auth_headers(token),
        json={
            "target_role": "Python backend developer",
            "difficulty": "intermediate",
            "interview_type": "technical",
            "question_count": 5,
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "CREATED"
    assert data["current_question_index"] == 0


def test_user_only_sees_own_interviews(client: TestClient) -> None:
    register_user(client, "first_user", "first@example.com")
    first_token = login_user(client, "first_user")
    register_user(client, "second_user", "second@example.com")
    second_token = login_user(client, "second_user")

    client.post(
        "/api/v1/interviews",
        headers=auth_headers(first_token),
        json={
            "target_role": "Python backend developer",
            "difficulty": "junior",
            "interview_type": "project",
            "question_count": 3,
        },
    )

    response = client.get("/api/v1/interviews", headers=auth_headers(second_token))

    assert response.status_code == 200
    assert response.json()["items"] == []
    assert response.json()["meta"]["total"] == 0


def test_user_cannot_access_other_users_interview(client: TestClient) -> None:
    register_user(client, "first_user", "first@example.com")
    first_token = login_user(client, "first_user")
    register_user(client, "second_user", "second@example.com")
    second_token = login_user(client, "second_user")

    create_response = client.post(
        "/api/v1/interviews",
        headers=auth_headers(first_token),
        json={
            "target_role": "Python backend developer",
            "difficulty": "senior",
            "interview_type": "comprehensive",
            "question_count": 8,
        },
    )
    session_id = create_response.json()["id"]

    response = client.get(
        f"/api/v1/interviews/{session_id}",
        headers=auth_headers(second_token),
    )

    assert response.status_code == 404
