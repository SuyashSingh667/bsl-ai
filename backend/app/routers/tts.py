from pathlib import Path
from fastapi import APIRouter

from app.schemas import TTSRequest, TTSResponse
from app.services import tts

router = APIRouter(prefix="/tts", tags=["tts"])


@router.post("", response_model=TTSResponse)
def synthesize(payload: TTSRequest):
    full_path = tts.synthesize(payload.text, payload.language)
    audio_url = f"/audio/{Path(full_path).name}" if full_path else ""
    return TTSResponse(audio_path=audio_url)
