from datetime import UTC, datetime, timedelta
from statistics import mean

from sqlalchemy import Select, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models.interview_knowledge_base_link import InterviewKnowledgeBaseLink
from app.models.interview_report import InterviewReport
from app.models.interview_session import InterviewSession
from app.models.user import User
from app.schemas.analytics import (
    AbilityAverages,
    AnalyticsHistoryItem,
    AnalyticsImprovementPlanItem,
    AnalyticsOverview,
    AnalyticsReportPoint,
    AnalyticsTrendItem,
    AnalyticsTrendResponse,
    WeakestDimension,
)
from app.schemas.common import PageMeta, PageResponse

DIMENSIONS = {
    "logic_score": ("逻辑结构", 25),
    "technical_score": ("技术准确性", 30),
    "expression_score": ("表达清晰度", 20),
    "project_depth_score": ("项目深度", 25),
}


def _completed_report_query(current_user: User) -> Select[tuple[InterviewSession]]:
    return (
        select(InterviewSession)
        .join(InterviewReport, InterviewReport.session_id == InterviewSession.id)
        .where(
            InterviewSession.user_id == current_user.id,
            InterviewSession.status == "COMPLETED",
        )
    )


def _round_score(value: float) -> float:
    return round(value, 2)


def _to_report_point(interview: InterviewSession) -> AnalyticsReportPoint:
    report = interview.report
    if report is None:
        raise ValueError("completed analytics query returned a session without report")
    return AnalyticsReportPoint(
        session_id=interview.id,
        target_role=interview.target_role,
        created_at=report.created_at,
        overall_score=report.overall_score,
        logic_score=report.logic_score,
        technical_score=report.technical_score,
        expression_score=report.expression_score,
        project_depth_score=report.project_depth_score,
    )


def _ability_averages(reports: list[InterviewReport]) -> AbilityAverages | None:
    if not reports:
        return None
    return AbilityAverages(
        logic_score=_round_score(mean(report.logic_score for report in reports)),
        technical_score=_round_score(mean(report.technical_score for report in reports)),
        expression_score=_round_score(mean(report.expression_score for report in reports)),
        project_depth_score=_round_score(mean(report.project_depth_score for report in reports)),
    )


def _weakest_dimension(reports: list[InterviewReport]) -> WeakestDimension | None:
    averages = _ability_averages(reports[:5])
    if averages is None:
        return None
    values = averages.model_dump()
    key = min(values, key=lambda name: values[name])
    label, max_score = DIMENSIONS[key]
    return WeakestDimension(
        key=key,
        label=label,
        average_score=values[key],
        max_score=max_score,
    )


def _latest_plan_items(report: InterviewReport | None) -> list[AnalyticsImprovementPlanItem]:
    if report is None:
        return []
    items: list[AnalyticsImprovementPlanItem] = []
    for raw_item in report.improvement_plan or []:
        if not isinstance(raw_item, dict):
            continue
        topic = raw_item.get("topic")
        if not topic:
            continue
        priority = raw_item.get("priority", "")
        items.append(
            AnalyticsImprovementPlanItem(
                priority=f"P{priority}" if isinstance(priority, int) else str(priority),
                topic=str(topic),
            )
        )
    return items


async def get_analytics_overview(
    session: AsyncSession,
    current_user: User,
) -> AnalyticsOverview:
    result = await session.execute(
        _completed_report_query(current_user)
        .options(joinedload(InterviewSession.report))
        .order_by(desc(InterviewReport.created_at))
    )
    interviews = list(result.scalars().unique())
    reports = [interview.report for interview in interviews if interview.report is not None]
    latest_interview = interviews[0] if interviews else None
    latest_report = latest_interview.report if latest_interview else None
    average_overall = (
        _round_score(mean(report.overall_score for report in reports)) if reports else 0
    )

    return AnalyticsOverview(
        completed_interview_count=len(interviews),
        average_overall_score=average_overall,
        latest_report=_to_report_point(latest_interview) if latest_interview else None,
        ability_averages=_ability_averages(reports),
        weakest_dimension=_weakest_dimension(reports),
        latest_improvement_plan=_latest_plan_items(latest_report),
    )


async def get_analytics_trend(
    session: AsyncSession,
    current_user: User,
    days: int,
    target_role: str | None = None,
) -> AnalyticsTrendResponse:
    since = datetime.now(UTC) - timedelta(days=days)
    query = (
        _completed_report_query(current_user)
        .options(joinedload(InterviewSession.report))
        .where(InterviewReport.created_at >= since)
    )
    if target_role:
        query = query.where(InterviewSession.target_role == target_role)
    result = await session.execute(query.order_by(InterviewReport.created_at.asc()))
    interviews = list(result.scalars().unique())
    return AnalyticsTrendResponse(
        items=[
            AnalyticsTrendItem(
                session_id=interview.id,
                target_role=interview.target_role,
                report_created_at=interview.report.created_at,
                overall_score=interview.report.overall_score,
                logic_score=interview.report.logic_score,
                technical_score=interview.report.technical_score,
                expression_score=interview.report.expression_score,
                project_depth_score=interview.report.project_depth_score,
            )
            for interview in interviews
            if interview.report is not None
        ]
    )


async def get_analytics_history(
    session: AsyncSession,
    current_user: User,
    page: int,
    page_size: int,
    target_role: str | None = None,
) -> PageResponse[AnalyticsHistoryItem]:
    base_query = _completed_report_query(current_user)
    count_query = (
        select(func.count())
        .select_from(InterviewSession)
        .join(InterviewReport, InterviewReport.session_id == InterviewSession.id)
        .where(
            InterviewSession.user_id == current_user.id,
            InterviewSession.status == "COMPLETED",
        )
    )
    if target_role:
        base_query = base_query.where(InterviewSession.target_role == target_role)
        count_query = count_query.where(InterviewSession.target_role == target_role)

    total = await session.scalar(count_query)
    result = await session.execute(
        base_query.options(
            joinedload(InterviewSession.report),
            selectinload(InterviewSession.knowledge_base_links).joinedload(
                InterviewKnowledgeBaseLink.knowledge_base
            ),
        )
        .order_by(desc(InterviewReport.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    interviews = list(result.scalars().unique())

    return PageResponse[AnalyticsHistoryItem](
        items=[
            AnalyticsHistoryItem(
                session_id=interview.id,
                target_role=interview.target_role,
                difficulty=interview.difficulty,
                interview_type=interview.interview_type,
                report_created_at=interview.report.created_at,
                overall_score=interview.report.overall_score,
                logic_score=interview.report.logic_score,
                technical_score=interview.report.technical_score,
                expression_score=interview.report.expression_score,
                project_depth_score=interview.report.project_depth_score,
                knowledge_base_names=[
                    link.knowledge_base.name
                    for link in interview.knowledge_base_links
                    if link.knowledge_base is not None
                ],
            )
            for interview in interviews
            if interview.report is not None
        ],
        meta=PageMeta(page=page, page_size=page_size, total=total or 0),
    )
