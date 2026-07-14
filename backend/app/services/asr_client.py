import logging
from pathlib import Path
from typing import Protocol

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.schemas.speech import AsrTranscriptionResult

ASR_NOT_CONFIGURED_MESSAGE = "ASR 服务尚未配置，请检查 ASR_API_KEY。"
ASR_FAILURE_MESSAGE = "云端 ASR 转写失败，请稍后重试。"

logger = logging.getLogger(__name__)


class AsrClient(Protocol):
    async def transcribe_wav(self, file_path: Path) -> AsrTranscriptionResult: ...


class DashScopeAsrClient:
    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    async def transcribe_wav(self, file_path: Path) -> AsrTranscriptionResult:
        try:
            import dashscope  # type: ignore[import-not-found]
        except ImportError as exc:
            raise AppError("ASR SDK 未安装，请安装 dashscope。", status_code=503) from exc

        audio_file_path = build_dashscope_file_url(file_path)
        try:
            dashscope.base_http_api_url = "https://dashscope.aliyuncs.com/api/v1"
            response = dashscope.MultiModalConversation.call(
                api_key=self.api_key,
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [{"audio": audio_file_path}],
                    }
                ],
                result_format="message",
                asr_options={
                    "language": "zh",
                    "enable_itn": False,
                },
            )
        except Exception as exc:
            logger.exception("DashScope ASR request failed. model=%s", self.model)
            raise AppError(ASR_FAILURE_MESSAGE, status_code=502) from exc

        if not _dashscope_response_is_success(response):
            logger.error(
                "DashScope ASR returned non-200. status_code=%s code=%s message=%s "
                "request_id=%s model=%s",
                getattr(response, "status_code", None),
                getattr(response, "code", None),
                getattr(response, "message", None),
                getattr(response, "request_id", None),
                self.model,
            )
            raise AppError(ASR_FAILURE_MESSAGE, status_code=502)

        text = _extract_transcription_text(response)
        if not text:
            raise AppError("ASR 未识别到有效文本，请重新录音。", status_code=422)
        return AsrTranscriptionResult(text=text, model=self.model, duration_seconds=None)


def build_dashscope_file_url(temp_path: Path) -> str:
    absolute_path = temp_path.resolve().as_posix()
    return f"file://{absolute_path}"


def _dashscope_response_is_success(response: object) -> bool:
    status_code = getattr(response, "status_code", None)
    code = getattr(response, "code", None)
    if status_code is not None:
        return int(status_code) == 200
    return code in (None, "", "Success", "success")


def _extract_transcription_text(response: object) -> str:
    output = getattr(response, "output", None)
    if isinstance(output, dict):
        return _extract_text_from_mapping(output)
    if isinstance(response, dict):
        return _extract_text_from_mapping(response)
    return ""


def _extract_text_from_mapping(payload: dict) -> str:
    direct_text = payload.get("text") or payload.get("transcription")
    if isinstance(direct_text, str):
        return direct_text.strip()

    for key in ("results", "sentences"):
        values = payload.get(key)
        if isinstance(values, list):
            parts = [
                item.get("text", "").strip()
                for item in values
                if isinstance(item, dict) and isinstance(item.get("text"), str)
            ]
            joined = "".join(parts).strip()
            if joined:
                return joined

    for key in ("task_result", "result"):
        nested = payload.get(key)
        if isinstance(nested, dict):
            text = _extract_text_from_mapping(nested)
            if text:
                return text
    choices = payload.get("choices")
    if isinstance(choices, list):
        for choice in choices:
            if isinstance(choice, dict):
                text = _extract_text_from_mapping(choice)
                if text:
                    return text
    message = payload.get("message")
    if isinstance(message, dict):
        text = _extract_text_from_mapping(message)
        if text:
            return text
    content = payload.get("content")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item.strip())
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"].strip())
        return "".join(parts).strip()
    return ""


def get_asr_client() -> AsrClient:
    settings = get_settings()
    if not settings.asr_api_key:
        raise AppError(ASR_NOT_CONFIGURED_MESSAGE, status_code=503)
    return DashScopeAsrClient(api_key=settings.asr_api_key, model=settings.asr_model)
