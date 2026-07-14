from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AppError
from app.models.answer_evaluation import AnswerEvaluation
from app.models.interview_answer import InterviewAnswer
from app.models.interview_question import InterviewQuestion
from app.models.user import User
from app.schemas.answer import AnswerHistoryItem, AnswerSubmitRequest, AnswerSubmitResponse
from app.schemas.evaluation import EvaluationResult
from app.services.agent_service import run_interview_agent
from app.services.embedding_client import EmbeddingClient
from app.services.expression_analysis import analyze_expression_quality, validate_evidence_items
from app.services.interview_service import get_own_interview_session
from app.services.llm_client import LLMClient
from app.services.question_service import get_primary_question_by_index, get_question_by_id
from app.services.retrieval_service import format_rag_context, retrieve_interview_rag_context


async def _get_question(session: AsyncSession, question_id: str) -> InterviewQuestion | None:
    result = await session.execute(
        select(InterviewQuestion).where(InterviewQuestion.id == question_id).limit(1)
    )
    return result.scalar_one_or_none()


async def _answer_exists(session: AsyncSession, question_id: str) -> bool:
    result = await session.execute(
        select(InterviewAnswer.id).where(InterviewAnswer.question_id == question_id).limit(1)
    )
    return result.scalar_one_or_none() is not None


async def _answered_count(session: AsyncSession, session_id: str) -> int:
    result = await session.execute(
        select(func.count())
        .select_from(InterviewAnswer)
        .where(InterviewAnswer.session_id == session_id)
    )
    return result.scalar_one()


def _build_evaluation_model(
    answer: InterviewAnswer,
    evaluation: EvaluationResult,
) -> AnswerEvaluation:
    evidence_items = validate_evidence_items(evaluation.evidence_items, answer.answer_text)
    expression_metrics = analyze_expression_quality(
        answer.answer_text,
        answer.recording_duration_seconds,
    )
    return AnswerEvaluation(
        answer_id=answer.id,
        total_score=evaluation.total_score,
        logic_score=evaluation.logic_score,
        technical_score=evaluation.technical_score,
        expression_score=evaluation.expression_score,
        project_depth_score=evaluation.project_depth_score,
        strengths=evaluation.strengths,
        weaknesses=evaluation.weaknesses,
        evidence_items_json=evidence_items,
        expression_metrics_json=expression_metrics,
        improvement_suggestion=evaluation.improvement_suggestion,
        detailed_feedback=evaluation.detailed_feedback,
    )


async def submit_answer_and_evaluate(
    session: AsyncSession,
    current_user: User,
    session_id: str,
    payload: AnswerSubmitRequest,
    llm_client: LLMClient,
    embedding_client: EmbeddingClient | None = None,
) -> AnswerSubmitResponse:
    interview = await get_own_interview_session(session, current_user, session_id)
    if interview is None:
        raise AppError("Interview session not found.", status_code=404)
    if interview.status != "IN_PROGRESS":
        raise AppError("Interview is not accepting answers.", status_code=409)

    question = await _get_question(session, payload.question_id)
    if question is None or question.session_id != interview.id:
        raise AppError("Interview question not found.", status_code=404)
    current_question = None
    if interview.current_question_id:
        current_question = await get_question_by_id(session, interview.current_question_id)
    if current_question is None:
        current_question = await get_primary_question_by_index(
            session,
            interview,
            interview.current_question_index,
        )
    if current_question is None:
        raise AppError("Interview questions have been completed.", status_code=409)
    if question.id != current_question.id:
        raise AppError("This is not the current question.", status_code=409)
    if await _answer_exists(session, question.id):
        raise AppError("This question has already been answered.", status_code=409)

    rag_context = "无"
    if embedding_client is not None:
        rag_items = await retrieve_interview_rag_context(
            session=session,
            interview=interview,
            query=f"{question.question_text}\n{payload.answer_text}",
            embedding_client=embedding_client,
        )
        rag_context = format_rag_context(rag_items)

    if rag_context == "无":
        evaluation_result = await llm_client.evaluate_answer(
            interview=interview,
            question=question,
            answer_text=payload.answer_text,
        )
    else:
        evaluation_result = await llm_client.evaluate_answer(
            interview=interview,
            question=question,
            answer_text=payload.answer_text,
            rag_context=rag_context,
        )

    answer = InterviewAnswer(
        session_id=interview.id,
        question_id=question.id,
        answer_text=payload.answer_text,
        recording_duration_seconds=payload.recording_duration_seconds,
    )
    try:
        session.add(answer)
        await session.flush()
        evaluation = _build_evaluation_model(answer, evaluation_result)
        session.add(evaluation)

        if question.question_type == "PRIMARY":
            interview.current_question_index += 1
        agent_action, reason_summary, next_question = await run_interview_agent(
            session=session,
            interview=interview,
            question=question,
            answer_text=payload.answer_text,
            evaluation=evaluation_result,
            llm_client=llm_client,
        )

        await session.commit()
    except Exception:
        await session.rollback()
        raise

    await session.refresh(answer)
    await session.refresh(evaluation)
    await session.refresh(interview)
    answered_count = await _answered_count(session, interview.id)
    return AnswerSubmitResponse(
        answer=answer,
        evaluation=evaluation,
        session_status=interview.status,
        answered_question_count=answered_count,
        question_count=interview.question_count,
        next_question=next_question,
        agent_action=agent_action,
        agent_reason_summary=reason_summary,
    )


async def list_answer_history(
    session: AsyncSession,
    current_user: User,
    session_id: str,
) -> list[AnswerHistoryItem]:
    interview = await get_own_interview_session(session, current_user, session_id)
    if interview is None:
        raise AppError("Interview session not found.", status_code=404)

    result = await session.execute(
        select(InterviewAnswer)
        .options(
            selectinload(InterviewAnswer.question),
            selectinload(InterviewAnswer.evaluation),
        )
        .join(InterviewQuestion, InterviewQuestion.id == InterviewAnswer.question_id)
        .where(InterviewAnswer.session_id == interview.id)
        .order_by(InterviewQuestion.sequence.asc())
    )
    answers = result.scalars().all()
    return [
        AnswerHistoryItem(
            question_id=answer.question_id,
            sequence=answer.question.sequence,
            category=answer.question.category,
            question_text=answer.question.question_text,
            question_type=answer.question.question_type,
            parent_question_id=answer.question.parent_question_id,
            answer_text=answer.answer_text,
            recording_duration_seconds=answer.recording_duration_seconds,
            evaluation=answer.evaluation,
            created_at=answer.created_at,
        )
        for answer in answers
        if answer.evaluation is not None
    ]
