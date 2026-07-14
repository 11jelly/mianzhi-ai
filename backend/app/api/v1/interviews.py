from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db_session
from app.models.interview_session import InterviewSession
from app.models.user import User
from app.schemas.agent import AgentEventRead
from app.schemas.answer import AnswerHistoryItem, AnswerSubmitRequest, AnswerSubmitResponse
from app.schemas.common import PageMeta, PageResponse
from app.schemas.interview import InterviewCreateRequest, InterviewSessionRead
from app.schemas.interview_question import InterviewQuestionRead, InterviewStartResponse
from app.schemas.report import InterviewReportRead
from app.services.agent_service import list_agent_events
from app.services.embedding_client import EmbeddingClient, get_embedding_client
from app.services.evaluation_service import list_answer_history, submit_answer_and_evaluate
from app.services.interview_service import (
    create_interview_session,
    get_own_interview_session,
    list_interview_sessions,
)
from app.services.llm_client import LLMClient, get_llm_client
from app.services.question_service import (
    get_current_question,
    get_questions,
    start_interview,
)
from app.services.report_service import generate_report, read_report

router = APIRouter(prefix="/interviews", tags=["interviews"])


@router.post(
    "",
    response_model=InterviewSessionRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_interview(
    payload: InterviewCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> InterviewSession:
    return await create_interview_session(session, current_user, payload)


@router.get("", response_model=PageResponse[InterviewSessionRead])
async def list_interviews(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
) -> PageResponse[InterviewSessionRead]:
    items, total = await list_interview_sessions(session, current_user, page, page_size)
    return PageResponse(
        items=items,
        meta=PageMeta(page=page, page_size=page_size, total=total),
    )


@router.get("/{session_id}", response_model=InterviewSessionRead)
async def get_interview(
    session_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> InterviewSession:
    interview = await get_own_interview_session(session, current_user, session_id)
    if interview is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview session not found.",
    )
    return interview


@router.post("/{session_id}/start", response_model=InterviewStartResponse)
async def start_text_interview(
    session_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    llm_client: Annotated[LLMClient, Depends(get_llm_client)],
    embedding_client: Annotated[EmbeddingClient, Depends(get_embedding_client)],
) -> InterviewStartResponse:
    return await start_interview(session, current_user, session_id, llm_client, embedding_client)


@router.get("/{session_id}/current-question", response_model=InterviewQuestionRead)
async def read_current_question(
    session_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    return await get_current_question(session, current_user, session_id)


@router.get("/{session_id}/questions", response_model=list[InterviewQuestionRead])
async def read_interview_questions(
    session_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list:
    return await get_questions(session, current_user, session_id)


@router.post("/{session_id}/answers", response_model=AnswerSubmitResponse)
async def submit_answer(
    session_id: str,
    payload: AnswerSubmitRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    llm_client: Annotated[LLMClient, Depends(get_llm_client)],
    embedding_client: Annotated[EmbeddingClient, Depends(get_embedding_client)],
) -> AnswerSubmitResponse:
    return await submit_answer_and_evaluate(
        session=session,
        current_user=current_user,
        session_id=session_id,
        payload=payload,
        llm_client=llm_client,
        embedding_client=embedding_client,
    )


@router.get("/{session_id}/answers", response_model=list[AnswerHistoryItem])
async def read_answers(
    session_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[AnswerHistoryItem]:
    return await list_answer_history(session, current_user, session_id)


@router.post("/{session_id}/report", response_model=InterviewReportRead)
async def create_report(
    session_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    llm_client: Annotated[LLMClient, Depends(get_llm_client)],
    embedding_client: Annotated[EmbeddingClient, Depends(get_embedding_client)],
) -> InterviewReportRead:
    return await generate_report(session, current_user, session_id, llm_client, embedding_client)


@router.get("/{session_id}/report", response_model=InterviewReportRead)
async def get_report(
    session_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> InterviewReportRead:
    return await read_report(session, current_user, session_id)


@router.get("/{session_id}/agent-events", response_model=list[AgentEventRead])
async def read_agent_events(
    session_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[AgentEventRead]:
    return await list_agent_events(session, current_user, session_id)
