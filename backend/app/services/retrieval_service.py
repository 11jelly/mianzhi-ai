from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.interview_session import InterviewSession
from app.schemas.knowledge_base import KnowledgeSearchItem, RagSource
from app.services.embedding_client import EmbeddingClient
from app.services.interview_service import get_interview_knowledge_base_ids
from app.services.knowledge_base_service import retrieve_knowledge_chunks


async def retrieve_interview_rag_context(
    session: AsyncSession,
    interview: InterviewSession,
    query: str,
    embedding_client: EmbeddingClient,
) -> list[dict]:
    knowledge_base_ids = await get_interview_knowledge_base_ids(session, interview.id)
    if not knowledge_base_ids:
        return []
    settings = get_settings()
    query_vector = (await embedding_client.embed_texts([query], input_type="query"))[0]
    items = await retrieve_knowledge_chunks(
        session=session,
        knowledge_base_ids=knowledge_base_ids,
        query_vector=query_vector,
        top_k=settings.rag_top_k,
    )
    return [item.model_dump() for item in items]


def format_rag_context(context_items: list[dict]) -> str:
    if not context_items:
        return "无"
    lines = []
    for index, item in enumerate(context_items, start=1):
        lines.append(
            f"{index}. 文档：{item.get('document_name')}；"
            f"相似度：{item.get('score')}；片段摘要：{item.get('content_preview')}"
        )
    return "\n".join(lines)


def to_rag_sources(items: list[KnowledgeSearchItem]) -> list[RagSource]:
    return [
        RagSource(
            knowledge_base_id="",
            knowledge_base_name="",
            document_name=item.document_name,
            content_preview=item.content_preview,
            score=item.score,
        )
        for item in items
    ]
