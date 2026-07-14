from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse


async def get_user_by_username_or_email(
    session: AsyncSession,
    username_or_email: str,
) -> User | None:
    result = await session.execute(
        select(User).where(
            or_(User.username == username_or_email, User.email == username_or_email)
        )
    )
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    return await session.get(User, user_id)


async def create_user(session: AsyncSession, payload: RegisterRequest) -> User:
    user = User(
        username=payload.username,
        email=str(payload.email),
        password_hash=hash_password(payload.password),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def username_or_email_exists(session: AsyncSession, username: str, email: str) -> bool:
    result = await session.execute(
        select(User.id).where(or_(User.username == username, User.email == email)).limit(1)
    )
    return result.scalar_one_or_none() is not None


async def authenticate_user(
    session: AsyncSession,
    payload: LoginRequest,
) -> User | None:
    user = await get_user_by_username_or_email(session, payload.username_or_email)
    if user is None or not user.is_active:
        return None
    if not verify_password(payload.password, user.password_hash):
        return None
    return user


def issue_token(user: User) -> TokenResponse:
    return TokenResponse(access_token=create_access_token(str(user.id)))
