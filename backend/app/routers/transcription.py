import shutil
import uuid

from fastapi import APIRouter, Form, UploadFile

from app.config import AUDIO_UPLOAD_DIR
from app.services import transcription

router = APIRouter(prefix="/transcription", tags=["transcription"])

AUDIO_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("")
def transcribe_audio(file: UploadFile, language: str | None = Form(None)):
    dest = AUDIO_UPLOAD_DIR / f"{uuid.uuid4().hex[:12]}_{file.filename}"
    with open(dest, "wb") as out:
        shutil.copyfileobj(file.file, out)

    lang_hint = language if (language and language != "auto") else None
    text, text_en, detected_lang, confidence = transcription.transcribe_and_translate(str(dest), language=lang_hint)
    return {
        "audio_path": str(dest),
        "transcript": text,
        "transcript_en": text_en,
        "language": detected_lang,
        "language_confidence": confidence,
    }

