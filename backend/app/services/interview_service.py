from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AppError
from app.models.interview_knowledge_base_link import InterviewKnowledgeBaseLink
from app.models.interview_report import InterviewReport
from app.models.interview_resume_link import InterviewResumeLink
from app.models.interview_session import InterviewSession
from app.models.knowledge_base import KnowledgeBase
from app.models.user import User
from app.schemas.interview import InterviewCreateRequest


async def create_interview_session(
    session: AsyncSession,
    current_user: User,
    payload: InterviewCreateRequest,
) -> InterviewSession:
    knowledge_base_ids = list(dict.fromkeys(payload.knowledge_base_ids))
    if knowledge_base_ids:
        await _validate_owned_knowledge_bases(session, current_user, knowledge_base_ids)
    interview = InterviewSession(
        user_id=current_user.id,
        target_role=payload.target_role,
        difficulty=payload.difficulty,
        interview_type=payload.interview_type,
        question_count=payload.question_count,
        use_active_resume=payload.use_active_resume,
        status="CREATED",
        current_question_index=0,
    )
    session.add(interview)
    await session.flush()
    session.add_all(
        [
            InterviewKnowledgeBaseLink(
                interview_session_id=interview.id,
                knowledge_base_id=knowledge_base_id,
            )
            for knowledge_base_id in knowledge_base_ids
        ]
    )
    await session.commit()
    return await _get_interview_with_knowledge_bases(session, interview.id) or interview


def _own_interviews_query(user_id: int) -> Select[tuple[InterviewSession]]:
    return (
        select(InterviewSession)
        .options(
            selectinload(InterviewSession.knowledge_base_links).selectinload(
                InterviewKnowledgeBaseLink.knowledge_base
            ),
            selectinload(InterviewSession.resume_link).selectinload(
                InterviewResumeLink.resume
            ),
        )
        .where(InterviewSession.user_id == user_id)
    )


async def list_interview_sessions(
    session: AsyncSession,
    current_user: User,
    page: int,
    page_size: int,
) -> tuple[list[InterviewSession], int]:
    base_query = _own_interviews_query(current_user.id)
    total_result = await session.execute(
        select(func.count()).select_from(base_query.subquery())
    )
    total = total_result.scalar_one()

    result = await session.execute(
        base_query.order_by(InterviewSession.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(result.scalars().all()), total


async def get_own_interview_session(
    session: AsyncSession,
    current_user: User,
    session_id: str,
) -> InterviewSession | None:
    result = await session.execute(
        select(InterviewSession).where(
            InterviewSession.id == session_id,
            InterviewSession.user_id == current_user.id,
        )
        .options(
            selectinload(InterviewSession.knowledge_base_links).selectinload(
                InterviewKnowledgeBaseLink.knowledge_base
            ),
            selectinload(InterviewSession.resume_link).selectinload(
                InterviewResumeLink.resume
            ),
        )
    )
    interview = result.scalar_one_or_none()
    if interview is None:
        return None
    await ensure_completed_status_when_report_exists(session, interview)
    return interview


async def ensure_completed_status_when_report_exists(
    session: AsyncSession,
    interview: InterviewSession,
) -> None:
    if interview.status == "COMPLETED":
        return
    result = await session.execute(
        select(InterviewReport.id)
        .where(InterviewReport.session_id == interview.id)
        .limit(1)
    )
    if result.scalar_one_or_none() is None:
        return
    interview.status = "COMPLETED"
    await session.commit()
    await session.refresh(interview)


async def get_interview_knowledge_base_ids(
    session: AsyncSession,
    interview_id: str,
) -> list[str]:
    result = await session.execute(
        select(InterviewKnowledgeBaseLink.knowledge_base_id).where(
            InterviewKnowledgeBaseLink.interview_session_id == interview_id
        )
    )
    return list(result.scalars().all())


async def _validate_owned_knowledge_bases(
    session: AsyncSession,
    current_user: User,
    knowledge_base_ids: list[str],
) -> None:
    result = await session.execute(
        select(KnowledgeBase.id).where(
            KnowledgeBase.id.in_(knowledge_base_ids),
            KnowledgeBase.owner_id == current_user.id,
        )
    )
    found_ids = set(result.scalars().all())
    if found_ids != set(knowledge_base_ids):
        raise AppError("Knowledge base not found.", status_code=404)


async def _get_interview_with_knowledge_bases(
    session: AsyncSession,
    interview_id: str,
) -> InterviewSession | None:
    result = await session.execute(
        select(InterviewSession)
        .where(InterviewSession.id == interview_id)
        .options(
            selectinload(InterviewSession.knowledge_base_links).selectinload(
                InterviewKnowledgeBaseLink.knowledge_base
            ),
            selectinload(InterviewSession.resume_link).selectinload(
                InterviewResumeLink.resume
            ),
        )
    )
    return result.scalar_one_or_none()
