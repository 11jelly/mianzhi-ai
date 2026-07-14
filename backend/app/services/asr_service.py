import logging
import tempfile
import wave
from pathlib import Path

from fastapi import UploadFile

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.schemas.speech import AsrTranscriptionResult
from app.services.asr_client import ASR_FAILURE_MESSAGE, AsrClient

WAV_HEADER_MIN_BYTES = 44

logger = logging.getLogger(__name__)


async def transcribe_uploaded_wav(
    audio: UploadFile,
    duration_seconds: float | None,
    asr_client: AsrClient,
) -> AsrTranscriptionResult:
    settings = get_settings()
    max_file_size_bytes = settings.asr_max_file_size_mb * 1024 * 1024
    if duration_seconds is not None and duration_seconds > settings.asr_max_duration_seconds:
        raise AppError("录音时长超过限制。", status_code=422)

    data = await audio.read(max_file_size_bytes + 1)
    if len(data) > max_file_size_bytes:
        raise AppError("音频文件过大。", status_code=413)
    if not data:
        raise AppError("音频文件为空。", status_code=422)
    if not _is_wav(data, audio.filename, audio.content_type):
        raise AppError("仅支持 WAV 音频文件。", status_code=422)

    temp_path = _write_temp_wav(data)
    try:
        _validate_temp_wav(temp_path)
        try:
            result = await asr_client.transcribe_wav(temp_path)
        except AppError:
            raise
        except Exception as exc:
            logger.exception("ASR provider failed while processing temporary WAV file.")
            raise AppError(ASR_FAILURE_MESSAGE, status_code=502) from exc
    finally:
        temp_path.unlink(missing_ok=True)

    if duration_seconds is not None and result.duration_seconds is None:
        return result.model_copy(update={"duration_seconds": duration_seconds})
    return result


def _is_wav(data: bytes, filename: str | None, content_type: str | None) -> bool:
    has_wav_header = (
        len(data) >= WAV_HEADER_MIN_BYTES
        and data[0:4] == b"RIFF"
        and data[8:12] == b"WAVE"
    )
    if not has_wav_header:
        return False
    if filename and not filename.lower().endswith(".wav"):
        return False
    if content_type and content_type not in {"audio/wav", "audio/wave", "audio/x-wav"}:
        return False
    return True


def _write_temp_wav(data: bytes) -> Path:
    with tempfile.NamedTemporaryFile(
        mode="wb",
        suffix=".wav",
        prefix="ai-interview-asr-",
        delete=False,
    ) as temp_file:
        temp_file.write(data)
        return Path(temp_file.name).resolve()


def _validate_temp_wav(temp_path: Path) -> None:
    if temp_path.suffix.lower() != ".wav":
        raise AppError("临时音频文件格式错误。", status_code=422)
    if not temp_path.exists():
        raise AppError("临时音频文件不存在。", status_code=422)
    file_size = temp_path.stat().st_size
    if file_size <= 0:
        raise AppError("音频文件为空。", status_code=422)
    try:
        with wave.open(str(temp_path), "rb") as wav_file:
            channels = wav_file.getnchannels()
            sample_rate = wav_file.getframerate()
            sample_width = wav_file.getsampwidth()
            frame_count = wav_file.getnframes()
    except wave.Error as exc:
        raise AppError("WAV 音频文件无法解析。", status_code=422) from exc
    logger.info(
        "Received ASR WAV metadata. file_size=%s sample_rate=%s channels=%s "
        "sample_width=%s frame_count=%s",
        file_size,
        sample_rate,
        channels,
        sample_width,
        frame_count,
    )
