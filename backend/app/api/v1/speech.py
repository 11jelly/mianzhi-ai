from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.speech import AsrTranscriptionResult
from app.services.asr_client import AsrClient, get_asr_client
from app.services.asr_service import transcribe_uploaded_wav

router = APIRouter(prefix="/speech", tags=["speech"])


@router.post("/transcriptions", response_model=AsrTranscriptionResult)
async def create_transcription(
    current_user: Annotated[User, Depends(get_current_user)],
    audio: Annotated[UploadFile, File()],
    asr_client: Annotated[AsrClient, Depends(get_asr_client)],
    duration_seconds: Annotated[float | None, Form()] = None,
) -> AsrTranscriptionResult:
    _ = current_user
    return await transcribe_uploaded_wav(audio, duration_seconds, asr_client)
