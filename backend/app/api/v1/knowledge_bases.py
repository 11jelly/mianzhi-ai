from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.knowledge_base import (
    KnowledgeBaseCreateRequest,
    KnowledgeBaseRead,
    KnowledgeDocumentRead,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
)
from app.services.embedding_client import EmbeddingClient, get_embedding_client
from app.services.knowledge_base_service import (
    create_knowledge_base,
    delete_knowledge_base,
    delete_knowledge_document,
    list_knowledge_bases,
    list_knowledge_documents,
    read_knowledge_base,
    search_knowledge_base,
    upload_knowledge_document,
)

router = APIRouter(prefix="/knowledge-bases", tags=["knowledge-bases"])


@router.post("", response_model=KnowledgeBaseRead, status_code=status.HTTP_201_CREATED)
async def create_base(
    payload: KnowledgeBaseCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> KnowledgeBaseRead:
    return await create_knowledge_base(session, current_user, payload)


@router.get("", response_model=list[KnowledgeBaseRead])
async def list_bases(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[KnowledgeBaseRead]:
    return await list_knowledge_bases(session, current_user)


@router.get("/{knowledge_base_id}", response_model=KnowledgeBaseRead)
async def get_base(
    knowledge_base_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> KnowledgeBaseRead:
    return await read_knowledge_base(session, current_user, knowledge_base_id)


@router.delete("/{knowledge_base_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_base(
    knowledge_base_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> None:
    await delete_knowledge_base(session, current_user, knowledge_base_id)


@router.post("/{knowledge_base_id}/documents", response_model=KnowledgeDocumentRead)
async def upload_document(
    knowledge_base_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    embedding_client: Annotated[EmbeddingClient, Depends(get_embedding_client)],
    file: Annotated[UploadFile, File()],
) -> KnowledgeDocumentRead:
    return await upload_knowledge_document(
        session,
        current_user,
        knowledge_base_id,
        file,
        embedding_client,
    )


@router.get("/{knowledge_base_id}/documents", response_model=list[KnowledgeDocumentRead])
async def list_documents(
    knowledge_base_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[KnowledgeDocumentRead]:
    return await list_knowledge_documents(session, current_user, knowledge_base_id)


@router.delete(
    "/{knowledge_base_id}/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_document(
    knowledge_base_id: str,
    document_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> None:
    await delete_knowledge_document(session, current_user, knowledge_base_id, document_id)


@router.post("/{knowledge_base_id}/search", response_model=KnowledgeSearchResponse)
async def search_base(
    knowledge_base_id: str,
    payload: KnowledgeSearchRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    embedding_client: Annotated[EmbeddingClient, Depends(get_embedding_client)],
) -> KnowledgeSearchResponse:
    return await search_knowledge_base(
        session=session,
        current_user=current_user,
        knowledge_base_id=knowledge_base_id,
        query=payload.query,
        top_k=payload.top_k,
        embedding_client=embedding_client,
    )
