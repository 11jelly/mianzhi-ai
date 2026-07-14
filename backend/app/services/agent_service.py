from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.interview_graph import build_interview_graph
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.models.interview_agent_event import InterviewAgentEvent
from app.models.interview_question import InterviewQuestion
from app.models.interview_session import InterviewSession
from app.models.user import User
from app.schemas.agent import AgentEventRead
from app.schemas.evaluation import EvaluationResult
from app.services.interview_service import get_own_interview_session
from app.services.llm_client import LLMClient
from app.services.question_service import get_primary_question_by_index
from app.services.resume_service import get_interview_resume_summary


async def has_follow_up_for_primary(session: AsyncSession, primary_question_id: str) -> bool:
    result = await session.execute(
        select(InterviewQuestion.id)
        .where(
            InterviewQuestion.parent_question_id == primary_question_id,
            InterviewQuestion.question_type == "FOLLOW_UP",
        )
        .limit(1)
    )
    return result.scalar_one_or_none() is not None


async def _next_sequence(session: AsyncSession, session_id: str) -> int:
    result = await session.execute(
        select(func.max(InterviewQuestion.sequence)).where(
            InterviewQuestion.session_id == session_id
        )
    )
    return (result.scalar_one_or_none() or 0) + 1


async def record_agent_event(
    session: AsyncSession,
    interview: InterviewSession,
    source_question_id: str,
    event_type: str,
    decision: str,
    reason_summary: str | None = None,
    follow_up_question_id: str | None = None,
) -> None:
    session.add(
        InterviewAgentEvent(
            session_id=interview.id,
            source_question_id=source_question_id,
            event_type=event_type,
            decision=decision,
            reason_summary=reason_summary,
            follow_up_question_id=follow_up_question_id,
        )
    )


async def run_interview_agent(
    session: AsyncSession,
    interview: InterviewSession,
    question: InterviewQuestion,
    answer_text: str,
    evaluation: EvaluationResult,
    llm_client: LLMClient,
) -> tuple[str, str | None, InterviewQuestion | None]:
    if question.question_type == "FOLLOW_UP":
        next_question = await _advance_to_next_primary_or_finish(session, interview)
        await record_agent_event(
            session,
            interview,
            question.id,
            "NEXT_PRIMARY" if next_question else "READY_FOR_REPORT",
            "NEXT_PRIMARY" if next_question else "READY_FOR_REPORT",
            "追问已完成，继续后续主问题。" if next_question else "全部主问题与追问已完成。",
        )
        return ("NEXT_PRIMARY" if next_question else "READY_FOR_REPORT", None, next_question)

    settings = get_settings()
    resume_link = await get_interview_resume_summary(session, interview.id)
    primary_already_has_follow_up = await has_follow_up_for_primary(session, question.id)
    max_per_primary = 0 if primary_already_has_follow_up else settings.max_follow_ups_per_primary
    state = {
        "session_id": interview.id,
        "question_id": question.id,
        "question_type": question.question_type,
        "parent_question_id": question.parent_question_id,
        "target_role": interview.target_role,
        "difficulty": interview.difficulty,
        "interview_type": interview.interview_type,
        "question_text": question.question_text,
        "answer_text": answer_text,
        "evaluation": evaluation.model_dump(),
        "current_question_index": interview.current_question_index,
        "question_count": interview.question_count,
        "follow_up_count": interview.follow_up_count,
        "max_follow_ups_per_session": settings.max_follow_ups_per_session,
        "max_follow_ups_per_primary": max_per_primary,
        "follow_up_min_score": settings.follow_up_min_score,
        "follow_up_score_threshold": settings.follow_up_score_threshold,
        "resume_context": resume_link.resume_context_snapshot if resume_link else "",
    }
    graph = build_interview_graph(llm_client)
    result = await graph.ainvoke(state)

    if result.get("agent_action") == "FOLLOW_UP" and result.get("follow_up_question"):
        follow_up = InterviewQuestion(
            session_id=interview.id,
            sequence=await _next_sequence(session, interview.id),
            category=result.get("follow_up_category") or "追问",
            question_text=result["follow_up_question"],
            expected_points=None,
            question_type="FOLLOW_UP",
            parent_question_id=question.id,
        )
        session.add(follow_up)
        await session.flush()
        interview.current_question_id = follow_up.id
        interview.follow_up_count += 1
        await record_agent_event(
            session,
            interview,
            question.id,
            "FOLLOW_UP_CREATED",
            "FOLLOW_UP",
            result.get("reason_summary"),
            follow_up.id,
        )
        return "FOLLOW_UP", result.get("reason_summary"), follow_up

    next_question = await _advance_to_next_primary_or_finish(session, interview)
    event_type = "NEXT_PRIMARY" if next_question else "READY_FOR_REPORT"
    reason = result.get("reason_summary") or "无需追问，继续流程。"
    await record_agent_event(session, interview, question.id, event_type, event_type, reason)
    return ("NEXT_PRIMARY" if next_question else "READY_FOR_REPORT", reason, next_question)


async def _advance_to_next_primary_or_finish(
    session: AsyncSession,
    interview: InterviewSession,
) -> InterviewQuestion | None:
    if interview.current_question_index >= interview.question_count:
        interview.status = "READY_FOR_REPORT"
        interview.current_question_id = None
        return None
    next_question = await get_primary_question_by_index(
        session,
        interview,
        interview.current_question_index,
    )
    if next_question is None:
        interview.status = "READY_FOR_REPORT"
        interview.current_question_id = None
        return None
    interview.current_question_id = next_question.id
    return next_question


async def list_agent_events(
    session: AsyncSession,
    current_user: User,
    session_id: str,
) -> list[AgentEventRead]:
    interview = await get_own_interview_session(session, current_user, session_id)
    if interview is None:
        raise AppError("Interview session not found.", status_code=404)
    result = await session.execute(
        select(InterviewAgentEvent)
        .where(InterviewAgentEvent.session_id == interview.id)
        .order_by(InterviewAgentEvent.created_at.asc())
    )
    return [AgentEventRead.model_validate(item) for item in result.scalars().all()]
