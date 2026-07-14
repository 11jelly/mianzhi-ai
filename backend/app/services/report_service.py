from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AppError
from app.models.interview_answer import InterviewAnswer
from app.models.interview_question import InterviewQuestion
from app.models.interview_report import InterviewReport
from app.models.user import User
from app.schemas.report import (
    AnswerEvidenceGroup,
    ExpressionAnalysisAnswerItem,
    ExpressionAnalysisReport,
    ExpressionAnalysisSummary,
    InterviewReportRead,
    ReportGenerationResult,
)
from app.services.embedding_client import EmbeddingClient
from app.services.interview_service import get_own_interview_session
from app.services.llm_client import LLMClient
from app.services.retrieval_service import format_rag_context, retrieve_interview_rag_context


def round_half_up_average(values: list[int]) -> int:
    if not values:
        raise ValueError("values must not be empty")
    total = sum(Decimal(value) for value in values)
    average = total / Decimal(len(values))
    return int(average.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def calculate_aggregate_scores(evaluations: list[Any]) -> dict[str, int]:
    return {
        "overall_score": round_half_up_average(
            [evaluation.total_score for evaluation in evaluations]
        ),
        "logic_score": round_half_up_average(
            [evaluation.logic_score for evaluation in evaluations]
        ),
        "technical_score": round_half_up_average(
            [evaluation.technical_score for evaluation in evaluations]
        ),
        "expression_score": round_half_up_average(
            [evaluation.expression_score for evaluation in evaluations]
        ),
        "project_depth_score": round_half_up_average(
            [evaluation.project_depth_score for evaluation in evaluations]
        ),
    }


async def get_report_by_session(
    session: AsyncSession,
    session_id: str,
) -> InterviewReport | None:
    result = await session.execute(
        select(InterviewReport).where(InterviewReport.session_id == session_id).limit(1)
    )
    return result.scalar_one_or_none()


async def _get_completed_answer_records(
    session: AsyncSession,
    session_id: str,
) -> list[InterviewAnswer]:
    result = await session.execute(
        select(InterviewAnswer)
        .options(
            selectinload(InterviewAnswer.question),
            selectinload(InterviewAnswer.evaluation),
        )
        .join(InterviewQuestion, InterviewQuestion.id == InterviewAnswer.question_id)
        .where(InterviewAnswer.session_id == session_id)
        .order_by(InterviewQuestion.sequence.asc())
    )
    return list(result.scalars().all())


def _build_prompt_records(answers: list[InterviewAnswer]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for answer in answers:
        evaluation = answer.evaluation
        question = answer.question
        if evaluation is None:
            continue
        records.append(
            {
                "sequence": question.sequence,
                "category": question.category,
                "question_type": question.question_type,
                "parent_question_id": question.parent_question_id,
                "question_text": question.question_text,
                "answer_text": answer.answer_text,
                "scores": {
                    "total_score": evaluation.total_score,
                    "logic_score": evaluation.logic_score,
                    "technical_score": evaluation.technical_score,
                    "expression_score": evaluation.expression_score,
                    "project_depth_score": evaluation.project_depth_score,
                },
                "strengths": evaluation.strengths,
                "weaknesses": evaluation.weaknesses,
                "improvement_suggestion": evaluation.improvement_suggestion,
                "detailed_feedback": evaluation.detailed_feedback,
            }
        )
    return records


def _build_report_model(
    session_id: str,
    scores: dict[str, int],
    content: ReportGenerationResult,
) -> InterviewReport:
    return InterviewReport(
        session_id=session_id,
        overall_score=scores["overall_score"],
        logic_score=scores["logic_score"],
        technical_score=scores["technical_score"],
        expression_score=scores["expression_score"],
        project_depth_score=scores["project_depth_score"],
        summary=content.summary,
        strengths=content.strengths,
        weaknesses=content.weaknesses,
        role_gap_analysis=content.role_gap_analysis,
        improvement_plan=[item.model_dump() for item in content.improvement_plan],
        next_practice_questions=content.next_practice_questions,
    )


def _build_answer_evidence(answers: list[InterviewAnswer]) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    for answer in answers:
        evaluation = answer.evaluation
        question = answer.question
        if evaluation is None or question is None:
            continue
        groups.append(
            AnswerEvidenceGroup(
                question_id=answer.question_id,
                sequence=question.sequence,
                category=question.category,
                question_text=question.question_text,
                question_type=question.question_type,
                parent_question_id=question.parent_question_id,
                answer_text=answer.answer_text,
                evidence_items=evaluation.evidence_items,
            ).model_dump()
        )
    return groups


def _build_expression_analysis(answers: list[InterviewAnswer]) -> dict[str, Any]:
    items: list[ExpressionAnalysisAnswerItem] = []
    for answer in answers:
        evaluation = answer.evaluation
        question = answer.question
        if evaluation is None or question is None:
            continue
        items.append(
            ExpressionAnalysisAnswerItem(
                question_id=answer.question_id,
                sequence=question.sequence,
                question_text=question.question_text,
                answer_text=answer.answer_text,
                recording_duration_seconds=answer.recording_duration_seconds,
                metrics=evaluation.expression_metrics,
            )
        )

    metrics = [item.metrics for item in items if item.metrics is not None]
    speech_rates = [
        metric.estimated_speech_rate
        for metric in metrics
        if metric.estimated_speech_rate is not None
    ]
    summary = ExpressionAnalysisSummary(
        average_answer_length=_average(
            [metric.character_count for metric in metrics],
        ),
        average_sentence_length=_average(
            [
                metric.average_sentence_length
                for metric in metrics
                if metric.average_sentence_length is not None
            ],
        ),
        total_filler_word_count=sum(metric.filler_word_count for metric in metrics)
        if metrics
        else None,
        total_structure_signal_count=sum(metric.structure_signal_count for metric in metrics)
        if metrics
        else None,
        average_estimated_speech_rate=_average(speech_rates),
        speech_rate_unit="字词/分钟" if speech_rates else None,
        sample_size=len(metrics),
        speech_rate_sample_size=len(speech_rates),
    )
    return ExpressionAnalysisReport(summary=summary, answers=items).model_dump()


def _average(values: list[float | int]) -> float | None:
    if not values:
        return None
    return round(sum(float(value) for value in values) / len(values), 2)


def _build_report_read(
    report: InterviewReport,
    answers: list[InterviewAnswer],
) -> InterviewReportRead:
    return InterviewReportRead(
        id=report.id,
        session_id=report.session_id,
        overall_score=report.overall_score,
        logic_score=report.logic_score,
        technical_score=report.technical_score,
        expression_score=report.expression_score,
        project_depth_score=report.project_depth_score,
        summary=report.summary,
        strengths=report.strengths,
        weaknesses=report.weaknesses,
        role_gap_analysis=report.role_gap_analysis,
        improvement_plan=report.improvement_plan,
        next_practice_questions=report.next_practice_questions,
        answer_evidence=_build_answer_evidence(answers),
        expression_analysis=_build_expression_analysis(answers),
        created_at=report.created_at,
        updated_at=report.updated_at,
    )


async def generate_report(
    session: AsyncSession,
    current_user: User,
    session_id: str,
    llm_client: LLMClient,
    embedding_client: EmbeddingClient | None = None,
) -> InterviewReportRead:
    interview = await get_own_interview_session(session, current_user, session_id)
    if interview is None:
        raise AppError("Interview session not found.", status_code=404)

    existing_report = await get_report_by_session(session, interview.id)
    if existing_report is not None:
        answers = await _get_completed_answer_records(session, interview.id)
        return _build_report_read(existing_report, answers)

    if interview.status == "COMPLETED":
        raise AppError("Interview report not found.", status_code=404)
    if interview.status != "READY_FOR_REPORT":
        raise AppError("Interview is not ready for report generation.", status_code=409)

    answers = await _get_completed_answer_records(session, interview.id)
    primary_answers = [
        answer for answer in answers if answer.question.question_type == "PRIMARY"
    ]
    evaluations = [
        answer.evaluation for answer in primary_answers if answer.evaluation is not None
    ]
    has_incomplete_primary_records = (
        len(primary_answers) != interview.question_count
        or len(evaluations) != interview.question_count
    )
    if has_incomplete_primary_records:
        raise AppError("Interview answers or evaluations are incomplete.", status_code=409)

    scores = calculate_aggregate_scores(evaluations)
    prompt_records = _build_prompt_records(answers)
    rag_context = "无"
    if embedding_client is not None:
        rag_items = await retrieve_interview_rag_context(
            session=session,
            interview=interview,
            query=f"{interview.target_role} 岗位能力要求 面试差距分析",
            embedding_client=embedding_client,
        )
        rag_context = format_rag_context(rag_items)
    if rag_context == "无":
        content = await llm_client.generate_interview_report(
            interview=interview,
            aggregate_scores=scores,
            records=prompt_records,
        )
    else:
        content = await llm_client.generate_interview_report(
            interview=interview,
            aggregate_scores=scores,
            records=prompt_records,
            rag_context=rag_context,
        )
    report = _build_report_model(interview.id, scores, content)

    try:
        session.add(report)
        interview.status = "COMPLETED"
        await session.commit()
    except IntegrityError:
        await session.rollback()
        existing_after_race = await get_report_by_session(session, interview.id)
        if existing_after_race is not None:
            answers = await _get_completed_answer_records(session, interview.id)
            return _build_report_read(existing_after_race, answers)
        raise
    except Exception:
        await session.rollback()
        raise

    await session.refresh(report)
    return _build_report_read(report, answers)


async def read_report(
    session: AsyncSession,
    current_user: User,
    session_id: str,
) -> InterviewReportRead:
    interview = await get_own_interview_session(session, current_user, session_id)
    if interview is None:
        raise AppError("Interview session not found.", status_code=404)

    report = await get_report_by_session(session, interview.id)
    if report is None:
        raise AppError("Interview report not found.", status_code=404)
    answers = await _get_completed_answer_records(session, interview.id)
    return _build_report_read(report, answers)
