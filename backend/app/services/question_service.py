import inspect

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.models.interview_question import InterviewQuestion
from app.models.interview_session import InterviewSession
from app.models.user import User
from app.schemas.interview_question import InterviewStartResponse
from app.schemas.llm import GeneratedQuestionSet
from app.services.embedding_client import EmbeddingClient
from app.services.interview_service import get_own_interview_session
from app.services.llm_client import LLMClient
from app.services.resume_service import build_resume_context_for_interview
from app.services.retrieval_service import (
    format_rag_context,
    retrieve_interview_rag_context,
)


async def list_questions_for_session(
    session: AsyncSession,
    interview: InterviewSession,
) -> list[InterviewQuestion]:
    result = await session.execute(
        select(InterviewQuestion)
        .where(InterviewQuestion.session_id == interview.id)
        .order_by(InterviewQuestion.sequence.asc())
    )
    return list(result.scalars().all())


async def get_question_by_id(
    session: AsyncSession,
    question_id: str,
) -> InterviewQuestion | None:
    result = await session.execute(
        select(InterviewQuestion).where(InterviewQuestion.id == question_id).limit(1)
    )
    return result.scalar_one_or_none()


async def get_current_question(
    session: AsyncSession,
    current_user: User,
    session_id: str,
) -> InterviewQuestion:
    interview = await get_own_interview_session(session, current_user, session_id)
    if interview is None:
        raise AppError("Interview session not found.", status_code=404)
    if interview.status in {"READY_FOR_REPORT", "COMPLETED"}:
        raise AppError("Interview questions have been completed.", status_code=409)
    if interview.status != "IN_PROGRESS":
        raise AppError("Interview has not been started.", status_code=409)
    if interview.current_question_id:
        question = await get_question_by_id(session, interview.current_question_id)
        if question is not None and question.session_id == interview.id:
            return question
    if interview.current_question_index >= interview.question_count:
        raise AppError("Interview questions have been completed.", status_code=409)

    question = await get_first_question(session, interview)
    if question is None:
        raise AppError("Interview questions are not available.", status_code=409)
    return question


async def get_first_question(
    session: AsyncSession,
    interview: InterviewSession,
) -> InterviewQuestion | None:
    result = await session.execute(
        select(InterviewQuestion)
        .where(
            InterviewQuestion.session_id == interview.id,
            InterviewQuestion.sequence == interview.current_question_index + 1,
            InterviewQuestion.question_type == "PRIMARY",
        )
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_primary_question_by_index(
    session: AsyncSession,
    interview: InterviewSession,
    primary_index: int,
) -> InterviewQuestion | None:
    result = await session.execute(
        select(InterviewQuestion)
        .where(
            InterviewQuestion.session_id == interview.id,
            InterviewQuestion.sequence == primary_index + 1,
            InterviewQuestion.question_type == "PRIMARY",
        )
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_questions(
    session: AsyncSession,
    current_user: User,
    session_id: str,
) -> list[InterviewQuestion]:
    interview = await get_own_interview_session(session, current_user, session_id)
    if interview is None:
        raise AppError("Interview session not found.", status_code=404)
    return await list_questions_for_session(session, interview)


async def _generate_interview_questions(
    llm_client: LLMClient,
    interview: InterviewSession,
    rag_context: str,
    resume_context: str,
) -> GeneratedQuestionSet:
    method = llm_client.generate_interview_questions
    parameter_names = inspect.signature(method).parameters
    if "resume_context" in parameter_names:
        return await method(
            interview,
            rag_context=rag_context,
            resume_context=resume_context,
        )
    if "rag_context" in parameter_names:
        return await method(interview, rag_context=rag_context)
    return await method(interview)


def _build_question_models(
    interview: InterviewSession,
    question_set: GeneratedQuestionSet,
) -> list[InterviewQuestion]:
    return [
        InterviewQuestion(
            session_id=interview.id,
            sequence=question.sequence,
            category=question.category,
            question_text=question.question_text,
            expected_points=question.expected_points,
        )
        for question in question_set.questions
    ]


async def start_interview(
    session: AsyncSession,
    current_user: User,
    session_id: str,
    llm_client: LLMClient,
    embedding_client: EmbeddingClient | None = None,
) -> InterviewStartResponse:
    interview = await get_own_interview_session(session, current_user, session_id)
    if interview is None:
        raise AppError("Interview session not found.", status_code=404)

    existing_questions = await list_questions_for_session(session, interview)
    if interview.status == "IN_PROGRESS" and existing_questions:
        current_question = None
        if interview.current_question_id:
            current_question = await get_question_by_id(session, interview.current_question_id)
        if current_question is None:
            current_question = await get_first_question(session, interview)
        current_response_question = (
            current_question or existing_questions[interview.current_question_index]
        )
        return InterviewStartResponse(
            session_id=interview.id,
            status="IN_PROGRESS",
            question_count=interview.question_count,
            current_question_index=interview.current_question_index,
            current_question=current_response_question,
        )

    if interview.status != "CREATED":
        raise AppError("Interview cannot be started in its current status.", status_code=409)

    try:
        query = f"{interview.target_role} {interview.difficulty} {interview.interview_type}"
        rag_context = "无"
        resume_context = ""
        if embedding_client is not None:
            rag_items = await retrieve_interview_rag_context(
                session=session,
                interview=interview,
                query=query,
                embedding_client=embedding_client,
            )
            rag_context = format_rag_context(rag_items)
            if interview.use_active_resume:
                resume_context = await build_resume_context_for_interview(
                    session=session,
                    interview_id=interview.id,
                    owner_id=current_user.id,
                    query=query,
                    embedding_client=embedding_client,
                )
        if not resume_context:
            question_set = await _generate_interview_questions(
                llm_client,
                interview,
                rag_context,
                "",
            )
        else:
            question_set = await _generate_interview_questions(
                llm_client,
                interview,
                rag_context,
                resume_context,
            )
        question_models = _build_question_models(interview, question_set)
        if existing_questions:
            await session.execute(
                delete(InterviewQuestion).where(InterviewQuestion.session_id == interview.id)
            )
        session.add_all(question_models)
        await session.flush()
        interview.status = "IN_PROGRESS"
        interview.current_question_index = 0
        interview.current_question_id = question_models[0].id
        await session.commit()
    except Exception:
        await session.rollback()
        raise

    first_question = question_models[0]
    await session.refresh(first_question)
    await session.refresh(interview)
    return InterviewStartResponse(
        session_id=interview.id,
        status="IN_PROGRESS",
        question_count=interview.question_count,
        current_question_index=interview.current_question_index,
        current_question=first_question,
    )
