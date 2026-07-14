import hashlib

from fastapi import UploadFile
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.models.knowledge_base import KnowledgeBase
from app.models.knowledge_chunk import KnowledgeChunk
from app.models.knowledge_document import KnowledgeDocument
from app.models.user import User
from app.schemas.knowledge_base import (
    KnowledgeBaseCreateRequest,
    KnowledgeBaseRead,
    KnowledgeDocumentRead,
    KnowledgeSearchItem,
    KnowledgeSearchResponse,
)
from app.services.document_parser import (
    extract_document_text,
    split_text_into_chunks,
    validate_document_size,
)
from app.services.embedding_client import EmbeddingClient
from app.services.vector_utils import cosine_similarity

MAX_CHUNKS_PER_KNOWLEDGE_BASE = 500


async def create_knowledge_base(
    session: AsyncSession,
    current_user: User,
    payload: KnowledgeBaseCreateRequest,
) -> KnowledgeBaseRead:
    knowledge_base = KnowledgeBase(
        owner_id=current_user.id,
        name=payload.name,
        description=payload.description,
    )
    session.add(knowledge_base)
    await session.commit()
    await session.refresh(knowledge_base)
    return await _build_knowledge_base_read(session, knowledge_base)


async def list_knowledge_bases(
    session: AsyncSession,
    current_user: User,
) -> list[KnowledgeBaseRead]:
    result = await session.execute(
        select(KnowledgeBase)
        .where(KnowledgeBase.owner_id == current_user.id)
        .order_by(KnowledgeBase.created_at.desc())
    )
    return [
        await _build_knowledge_base_read(session, knowledge_base)
        for knowledge_base in result.scalars().all()
    ]


async def get_knowledge_base_for_user(
    session: AsyncSession,
    current_user: User,
    knowledge_base_id: str,
) -> KnowledgeBase | None:
    result = await session.execute(
        select(KnowledgeBase)
        .where(
            KnowledgeBase.id == knowledge_base_id,
            KnowledgeBase.owner_id == current_user.id,
        )
        .limit(1)
    )
    return result.scalar_one_or_none()


async def read_knowledge_base(
    session: AsyncSession,
    current_user: User,
    knowledge_base_id: str,
) -> KnowledgeBaseRead:
    knowledge_base = await get_knowledge_base_for_user(session, current_user, knowledge_base_id)
    if knowledge_base is None:
        raise AppError("Knowledge base not found.", status_code=404)
    return await _build_knowledge_base_read(session, knowledge_base)


async def delete_knowledge_base(
    session: AsyncSession,
    current_user: User,
    knowledge_base_id: str,
) -> None:
    knowledge_base = await get_knowledge_base_for_user(session, current_user, knowledge_base_id)
    if knowledge_base is None:
        raise AppError("Knowledge base not found.", status_code=404)
    await session.delete(knowledge_base)
    await session.commit()


async def upload_knowledge_document(
    session: AsyncSession,
    current_user: User,
    knowledge_base_id: str,
    file: UploadFile,
    embedding_client: EmbeddingClient,
) -> KnowledgeDocumentRead:
    knowledge_base = await get_knowledge_base_for_user(session, current_user, knowledge_base_id)
    if knowledge_base is None:
        raise AppError("Knowledge base not found.", status_code=404)

    content = await file.read()
    validate_document_size(content)
    filename = file.filename or "uploaded-document"
    text, file_type = extract_document_text(filename, content)
    content_hash = hashlib.sha256(content).hexdigest()
    if await _document_hash_exists(session, knowledge_base.id, content_hash):
        raise AppError("同一知识库中已存在相同内容的文档。", status_code=409)

    chunks = split_text_into_chunks(text)
    if not chunks:
        raise AppError("文档未切分出有效片段。", status_code=422)
    existing_chunk_count = await _chunk_count_for_knowledge_base(session, knowledge_base.id)
    if existing_chunk_count + len(chunks) > MAX_CHUNKS_PER_KNOWLEDGE_BASE:
        raise AppError("知识库 chunk 数量超过上限。", status_code=409)

    document = KnowledgeDocument(
        knowledge_base_id=knowledge_base.id,
        original_filename=filename[:255],
        file_type=file_type,
        content_hash=content_hash,
        extracted_text_length=len(text),
        status="PROCESSING",
    )
    session.add(document)
    await session.flush()

    try:
        embeddings = await embedding_client.embed_texts(chunks, input_type="document")
        settings = get_settings()
        session.add_all(
            [
                KnowledgeChunk(
                    document_id=document.id,
                    chunk_index=index,
                    content=chunk,
                    embedding=embedding,
                    embedding_model=settings.embedding_model,
                    embedding_dimension=len(embedding),
                    chunk_metadata={"source": "document"},
                )
                for index, (chunk, embedding) in enumerate(
                    zip(chunks, embeddings, strict=True)
                )
            ]
        )
        document.status = "READY"
        await session.commit()
    except Exception as exc:
        await session.execute(
            delete(KnowledgeChunk).where(KnowledgeChunk.document_id == document.id)
        )
        document.status = "FAILED"
        document.error_message = "文档向量化失败，请稍后重试。"
        await session.commit()
        if isinstance(exc, AppError):
            raise
        raise AppError("文档向量化失败，请稍后重试。", status_code=502) from exc

    await session.refresh(document)
    return await _build_document_read(session, document)


async def list_knowledge_documents(
    session: AsyncSession,
    current_user: User,
    knowledge_base_id: str,
) -> list[KnowledgeDocumentRead]:
    knowledge_base = await get_knowledge_base_for_user(session, current_user, knowledge_base_id)
    if knowledge_base is None:
        raise AppError("Knowledge base not found.", status_code=404)
    result = await session.execute(
        select(KnowledgeDocument)
        .where(KnowledgeDocument.knowledge_base_id == knowledge_base.id)
        .order_by(KnowledgeDocument.created_at.desc())
    )
    return [await _build_document_read(session, document) for document in result.scalars().all()]


async def delete_knowledge_document(
    session: AsyncSession,
    current_user: User,
    knowledge_base_id: str,
    document_id: str,
) -> None:
    knowledge_base = await get_knowledge_base_for_user(session, current_user, knowledge_base_id)
    if knowledge_base is None:
        raise AppError("Knowledge base not found.", status_code=404)
    result = await session.execute(
        select(KnowledgeDocument).where(
            KnowledgeDocument.id == document_id,
            KnowledgeDocument.knowledge_base_id == knowledge_base.id,
        )
    )
    document = result.scalar_one_or_none()
    if document is None:
        raise AppError("Knowledge document not found.", status_code=404)
    await session.delete(document)
    await session.commit()


async def search_knowledge_base(
    session: AsyncSession,
    current_user: User,
    knowledge_base_id: str,
    query: str,
    top_k: int | None,
    embedding_client: EmbeddingClient,
) -> KnowledgeSearchResponse:
    knowledge_base = await get_knowledge_base_for_user(session, current_user, knowledge_base_id)
    if knowledge_base is None:
        raise AppError("Knowledge base not found.", status_code=404)
    settings = get_settings()
    query_vector = (await embedding_client.embed_texts([query], input_type="query"))[0]
    items = await retrieve_knowledge_chunks(
        session=session,
        knowledge_base_ids=[knowledge_base.id],
        query_vector=query_vector,
        top_k=top_k or settings.rag_top_k,
    )
    return KnowledgeSearchResponse(items=items)


async def retrieve_knowledge_chunks(
    session: AsyncSession,
    knowledge_base_ids: list[str],
    query_vector: list[float],
    top_k: int,
) -> list[KnowledgeSearchItem]:
    if not knowledge_base_ids:
        return []
    result = await session.execute(
        select(KnowledgeChunk)
        .options(selectinload(KnowledgeChunk.document))
        .join(KnowledgeDocument, KnowledgeDocument.id == KnowledgeChunk.document_id)
        .where(
            KnowledgeDocument.knowledge_base_id.in_(knowledge_base_ids),
            KnowledgeDocument.status == "READY",
        )
    )
    scored: list[tuple[float, KnowledgeChunk]] = []
    for chunk in result.scalars().all():
        scored.append((cosine_similarity(query_vector, chunk.embedding), chunk))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [
        KnowledgeSearchItem(
            chunk_id=chunk.id,
            document_name=chunk.document.original_filename,
            content_preview=chunk.content[:300],
            score=round(score, 6),
        )
        for score, chunk in scored[:top_k]
    ]


async def _document_hash_exists(
    session: AsyncSession,
    knowledge_base_id: str,
    content_hash: str,
) -> bool:
    result = await session.execute(
        select(KnowledgeDocument.id)
        .where(
            KnowledgeDocument.knowledge_base_id == knowledge_base_id,
            KnowledgeDocument.content_hash == content_hash,
        )
        .limit(1)
    )
    return result.scalar_one_or_none() is not None


async def _chunk_count_for_knowledge_base(session: AsyncSession, knowledge_base_id: str) -> int:
    result = await session.execute(
        select(func.count())
        .select_from(KnowledgeChunk)
        .join(KnowledgeDocument, KnowledgeDocument.id == KnowledgeChunk.document_id)
        .where(KnowledgeDocument.knowledge_base_id == knowledge_base_id)
    )
    return result.scalar_one()


async def _build_knowledge_base_read(
    session: AsyncSession,
    knowledge_base: KnowledgeBase,
) -> KnowledgeBaseRead:
    document_count_result = await session.execute(
        select(func.count())
        .select_from(KnowledgeDocument)
        .where(KnowledgeDocument.knowledge_base_id == knowledge_base.id)
    )
    chunk_count_result = await session.execute(
        select(func.count())
        .select_from(KnowledgeChunk)
        .join(KnowledgeDocument, KnowledgeDocument.id == KnowledgeChunk.document_id)
        .where(KnowledgeDocument.knowledge_base_id == knowledge_base.id)
    )
    failed_result = await session.execute(
        select(func.count())
        .select_from(KnowledgeDocument)
        .where(
            KnowledgeDocument.knowledge_base_id == knowledge_base.id,
            KnowledgeDocument.status == "FAILED",
        )
    )
    document_count = document_count_result.scalar_one()
    chunk_count = chunk_count_result.scalar_one()
    failed_count = failed_result.scalar_one()
    status = "EMPTY"
    if failed_count:
        status = "FAILED"
    elif document_count:
        status = "READY"
    return KnowledgeBaseRead(
        id=knowledge_base.id,
        name=knowledge_base.name,
        description=knowledge_base.description,
        document_count=document_count,
        chunk_count=chunk_count,
        status=status,
        created_at=knowledge_base.created_at,
        updated_at=knowledge_base.updated_at,
    )


async def _build_document_read(
    session: AsyncSession,
    document: KnowledgeDocument,
) -> KnowledgeDocumentRead:
    chunk_count_result = await session.execute(
        select(func.count())
        .select_from(KnowledgeChunk)
        .where(KnowledgeChunk.document_id == document.id)
    )
    return KnowledgeDocumentRead(
        id=document.id,
        knowledge_base_id=document.knowledge_base_id,
        original_filename=document.original_filename,
        file_type=document.file_type,
        content_hash=document.content_hash,
        extracted_text_length=document.extracted_text_length,
        status=document.status,
        error_message=document.error_message,
        chunk_count=chunk_count_result.scalar_one(),
        created_at=document.created_at,
        updated_at=document.updated_at,
    )
