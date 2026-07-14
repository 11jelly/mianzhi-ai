from typing import Literal, Protocol

from openai import APIConnectionError, APITimeoutError, AsyncOpenAI, OpenAIError

from app.core.config import get_settings
from app.core.exceptions import AppError

EMBEDDING_NOT_CONFIGURED_MESSAGE = "Embedding 服务尚未配置，请检查 EMBEDDING_API_KEY。"
EMBEDDING_FAILURE_MESSAGE = "Embedding 服务暂时不可用，请稍后重试。"
EmbeddingInputType = Literal["document", "query"]


class EmbeddingClient(Protocol):
    async def embed_texts(
        self,
        texts: list[str],
        input_type: EmbeddingInputType,
    ) -> list[list[float]]: ...


class BailianEmbeddingClient:
    async def embed_texts(
        self,
        texts: list[str],
        input_type: EmbeddingInputType,
    ) -> list[list[float]]:
        settings = get_settings()
        if not settings.embedding_api_key:
            raise AppError(EMBEDDING_NOT_CONFIGURED_MESSAGE, status_code=503)
        if not settings.llm_base_url:
            raise AppError("Embedding base URL 未配置。", status_code=503)
        client = AsyncOpenAI(
            api_key=settings.embedding_api_key,
            base_url=settings.llm_base_url,
            timeout=45.0,
        )
        try:
            response = await client.embeddings.create(
                model=settings.embedding_model,
                input=texts,
                extra_body={"input_type": input_type},
            )
        except (APITimeoutError, APIConnectionError) as exc:
            raise AppError("Embedding 服务连接超时或网络异常。", status_code=503) from exc
        except OpenAIError as exc:
            raise AppError(EMBEDDING_FAILURE_MESSAGE, status_code=502) from exc
        embeddings = [item.embedding for item in response.data]
        if len(embeddings) != len(texts):
            raise AppError("Embedding 返回数量不匹配。", status_code=502)
        expected_dimension = settings.embedding_dimension
        if any(len(vector) != expected_dimension for vector in embeddings):
            raise AppError("Embedding 维度不符合配置。", status_code=502)
        return embeddings


def get_embedding_client() -> EmbeddingClient:
    return BailianEmbeddingClient()
