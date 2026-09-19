from fastapi import APIRouter

from app.schemas import TTSRequest, TTSResponse
from app.services import tts

router = APIRouter(prefix="/tts", tags=["tts"])


@router.post("", response_model=TTSResponse)
def synthesize(payload: TTSRequest):
    audio_path = tts.synthesize(payload.text, payload.language)
    return TTSResponse(audio_path=audio_path)
