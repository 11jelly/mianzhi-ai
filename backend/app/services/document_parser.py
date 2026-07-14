from io import BytesIO
from pathlib import Path

from app.core.config import get_settings
from app.core.exceptions import AppError

ALLOWED_DOCUMENT_EXTENSIONS = {".txt", ".md", ".pdf"}


def extract_document_text(filename: str, content: bytes) -> tuple[str, str]:
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_DOCUMENT_EXTENSIONS:
        raise AppError("仅支持 txt、md、pdf 文件。", status_code=422)
    if not content:
        raise AppError("上传文件为空。", status_code=422)
    if suffix in {".txt", ".md"}:
        text = content.decode("utf-8", errors="ignore")
    else:
        text = _extract_pdf_text(content)
    normalized = normalize_text(text)
    if not normalized:
        raise AppError("文档未提取到有效文本。", status_code=422)
    return normalized, suffix.lstrip(".")


def validate_document_size(content: bytes) -> None:
    settings = get_settings()
    max_size = settings.rag_max_document_size_mb * 1024 * 1024
    if len(content) > max_size:
        raise AppError("文档文件过大。", status_code=413)


def split_text_into_chunks(text: str) -> list[str]:
    settings = get_settings()
    chunk_size = settings.rag_chunk_size
    overlap = min(settings.rag_chunk_overlap, max(chunk_size // 2, 0))
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            split_at = _find_boundary(text, start, end)
            if split_at > start:
                end = split_at
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks


def normalize_text(text: str) -> str:
    lines = [line.strip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    compact_lines = [line for line in lines if line]
    return "\n".join(compact_lines).strip()


def _find_boundary(text: str, start: int, end: int) -> int:
    window = text[start:end]
    for marker in ("\n\n", "\n", "。", "！", "？", ".", "!", "?"):
        index = window.rfind(marker)
        if index >= int(len(window) * 0.5):
            return start + index + len(marker)
    return end


def _extract_pdf_text(content: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise AppError("PDF 解析依赖未安装，请安装 pypdf。", status_code=503) from exc
    try:
        reader = PdfReader(BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as exc:
        raise AppError("PDF 文档解析失败。", status_code=422) from exc
