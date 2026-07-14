from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.analytics import (
    AnalyticsHistoryItem,
    AnalyticsOverview,
    AnalyticsTrendResponse,
)
from app.schemas.common import PageResponse
from app.services.analytics_service import (
    get_analytics_history,
    get_analytics_overview,
    get_analytics_trend,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview", response_model=AnalyticsOverview)
async def analytics_overview(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AnalyticsOverview:
    return await get_analytics_overview(session, current_user)


@router.get("/trend", response_model=AnalyticsTrendResponse)
async def analytics_trend(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    days: Annotated[int, Query()] = 90,
    target_role: str | None = None,
) -> AnalyticsTrendResponse:
    allowed_days = {30, 90, 180, 365}
    normalized_days = days if days in allowed_days else 90
    return await get_analytics_trend(session, current_user, normalized_days, target_role)


@router.get("/history", response_model=PageResponse[AnalyticsHistoryItem])
async def analytics_history(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 10,
    target_role: str | None = None,
) -> PageResponse[AnalyticsHistoryItem]:
    return await get_analytics_history(session, current_user, page, page_size, target_role)
