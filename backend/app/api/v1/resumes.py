from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.resume import ResumePasteRequest, ResumeRead, ResumeUpdateRequest
from app.services.embedding_client import EmbeddingClient, get_embedding_client
from app.services.resume_service import (
    activate_resume,
    deactivate_resume,
    delete_resume,
    list_resumes,
    paste_resume,
    read_resume,
    update_resume,
    upload_resume,
)

router = APIRouter(prefix="/resumes", tags=["resumes"])


@router.get("", response_model=list[ResumeRead])
async def list_my_resumes(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[ResumeRead]:
    return await list_resumes(session, current_user)


@router.get("/{resume_id}", response_model=ResumeRead)
async def get_my_resume(
    resume_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ResumeRead:
    return await read_resume(session, current_user, resume_id)


@router.post("/paste", response_model=ResumeRead, status_code=status.HTTP_201_CREATED)
async def create_resume_from_text(
    payload: ResumePasteRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    embedding_client: Annotated[EmbeddingClient, Depends(get_embedding_client)],
) -> ResumeRead:
    return await paste_resume(session, current_user, payload, embedding_client)


@router.post("/upload", response_model=ResumeRead, status_code=status.HTTP_201_CREATED)
async def upload_my_resume(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    embedding_client: Annotated[EmbeddingClient, Depends(get_embedding_client)],
    file: Annotated[UploadFile, File()],
    title: Annotated[str | None, Form()] = None,
    activate: Annotated[bool, Form()] = True,
) -> ResumeRead:
    return await upload_resume(session, current_user, title, activate, file, embedding_client)


@router.patch("/{resume_id}", response_model=ResumeRead)
async def update_my_resume(
    resume_id: str,
    payload: ResumeUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ResumeRead:
    return await update_resume(session, current_user, resume_id, payload)


@router.post("/{resume_id}/activate", response_model=ResumeRead)
async def activate_my_resume(
    resume_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ResumeRead:
    return await activate_resume(session, current_user, resume_id)


@router.post("/{resume_id}/deactivate", response_model=ResumeRead)
async def deactivate_my_resume(
    resume_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ResumeRead:
    return await deactivate_resume(session, current_user, resume_id)


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_resume(
    resume_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> None:
    await delete_resume(session, current_user, resume_id)
