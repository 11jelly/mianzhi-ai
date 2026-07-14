import asyncio
import struct
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.core.exceptions import AppError
from app.db.session import get_db_session
from app.models.answer_evaluation import AnswerEvaluation
from app.models.interview_answer import InterviewAnswer
from app.models.interview_session import InterviewSession
from app.schemas.speech import AsrTranscriptionResult
from app.services.asr_client import (
    ASR_NOT_CONFIGURED_MESSAGE,
    build_dashscope_file_url,
    get_asr_client,
)
from tests.test_phase1_auth_interviews import auth_headers, login_user, register_user
from tests.test_phase2a_questions import create_interview

pytest_plugins = ["tests.test_phase1_auth_interviews"]


class FakeAsrClient:
    def __init__(self, text: str = "这是 Fake ASR 转写文本。") -> None:
        self.text = text
        self.calls = 0
        self.paths: list[Path] = []

    async def transcribe_wav(self, file_path: Path) -> AsrTranscriptionResult:
        self.calls += 1
        self.paths.append(file_path)
        return AsrTranscriptionResult(
            text=self.text,
            model="fake-asr",
            duration_seconds=None,
        )


class FailingAsrClient:
    def __init__(self) -> None:
        self.paths: list[Path] = []

    async def transcribe_wav(self, file_path: Path) -> AsrTranscriptionResult:
        self.paths.append(file_path)
        raise RuntimeError("fake provider failure")


def build_wav_bytes(duration_seconds: float = 0.1, sample_rate: int = 16000) -> bytes:
    sample_count = int(duration_seconds * sample_rate)
    pcm = b"\x00\x00" * sample_count
    byte_rate = sample_rate * 2
    block_align = 2
    return b"".join(
        [
            b"RIFF",
            struct.pack("<I", 36 + len(pcm)),
            b"WAVE",
            b"fmt ",
            struct.pack("<IHHIIHH", 16, 1, 1, sample_rate, byte_rate, block_align, 16),
            b"data",
            struct.pack("<I", len(pcm)),
            pcm,
        ]
    )


def override_asr(client: TestClient, fake_asr) -> None:
    client.app.dependency_overrides[get_asr_client] = lambda: fake_asr


def post_transcription(
    client: TestClient,
    token: str | None,
    content: bytes,
    filename: str = "answer.wav",
    content_type: str = "audio/wav",
    duration_seconds: float | None = 0.1,
):
    headers = auth_headers(token) if token else {}
    data = {}
    if duration_seconds is not None:
        data["duration_seconds"] = str(duration_seconds)
    return client.post(
        "/api/v1/speech/transcriptions",
        headers=headers,
        data=data,
        files={"audio": (filename, content, content_type)},
    )


def read_counts_and_session_status(client: TestClient, session_id: str) -> tuple[int, int, str]:
    async def read_state() -> tuple[int, int, str]:
        override = client.app.dependency_overrides[get_db_session]
        async for session in override():
            answer_count = (
                await session.execute(select(func.count()).select_from(InterviewAnswer))
            ).scalar_one()
            evaluation_count = (
                await session.execute(select(func.count()).select_from(AnswerEvaluation))
            ).scalar_one()
            status_value = (
                await session.execute(
                    select(InterviewSession.status).where(InterviewSession.id == session_id)
                )
            ).scalar_one()
            return answer_count, evaluation_count, status_value
        raise AssertionError("database session override did not yield")

    return asyncio.run(read_state())


def test_logged_in_user_can_upload_wav_and_receive_fake_transcription(
    client: TestClient,
) -> None:
    register_user(client)
    token = login_user(client)
    fake_asr = FakeAsrClient()
    override_asr(client, fake_asr)

    response = post_transcription(client, token, build_wav_bytes(), duration_seconds=2.5)

    assert response.status_code == 200
    assert response.json() == {
        "text": "这是 Fake ASR 转写文本。",
        "model": "fake-asr",
        "duration_seconds": 2.5,
    }
    assert fake_asr.calls == 1
    assert fake_asr.paths[0].exists() is False


def test_windows_path_is_converted_to_dashscope_file_url() -> None:
    audio_file_url = build_dashscope_file_url(Path(r"D:\temp\audio.wav"))

    assert audio_file_url == "file://D:/temp/audio.wav"
    assert audio_file_url != "file:///D:/temp/audio.wav"


def test_transcription_requires_login(client: TestClient) -> None:
    override_asr(client, FakeAsrClient())

    response = post_transcription(client, None, build_wav_bytes())

    assert response.status_code == 401


def test_empty_audio_returns_422(client: TestClient) -> None:
    register_user(client)
    token = login_user(client)
    override_asr(client, FakeAsrClient())

    response = post_transcription(client, token, b"")

    assert response.status_code == 422


def test_non_wav_audio_returns_422(client: TestClient) -> None:
    register_user(client)
    token = login_user(client)
    override_asr(client, FakeAsrClient())

    response = post_transcription(
        client,
        token,
        b"not a wav",
        filename="answer.webm",
        content_type="audio/webm",
    )

    assert response.status_code == 422


def test_audio_larger_than_limit_returns_413(client: TestClient) -> None:
    register_user(client)
    token = login_user(client)
    override_asr(client, FakeAsrClient())
    oversized_wav = build_wav_bytes() + (b"\x00" * (11 * 1024 * 1024))

    response = post_transcription(client, token, oversized_wav)

    assert response.status_code == 413


def test_missing_asr_configuration_returns_503(client: TestClient) -> None:
    register_user(client)
    token = login_user(client)

    def raise_not_configured():
        raise AppError(ASR_NOT_CONFIGURED_MESSAGE, status_code=503)

    client.app.dependency_overrides[get_asr_client] = raise_not_configured

    response = post_transcription(client, token, build_wav_bytes())

    assert response.status_code == 503
    assert response.json()["detail"] == ASR_NOT_CONFIGURED_MESSAGE


def test_asr_provider_failure_returns_502(client: TestClient) -> None:
    register_user(client)
    token = login_user(client)
    fake_asr = FailingAsrClient()
    override_asr(client, fake_asr)

    response = post_transcription(client, token, build_wav_bytes())

    assert response.status_code == 502
    assert fake_asr.paths[0].exists() is False


def test_asr_endpoint_does_not_create_or_modify_interview_records(
    client: TestClient,
) -> None:
    register_user(client)
    token = login_user(client)
    session_id = create_interview(client, token, question_count=3)
    before = read_counts_and_session_status(client, session_id)
    override_asr(client, FakeAsrClient())

    response = post_transcription(client, token, build_wav_bytes())
    after = read_counts_and_session_status(client, session_id)

    assert response.status_code == 200
    assert before == (0, 0, "CREATED")
    assert after == before
