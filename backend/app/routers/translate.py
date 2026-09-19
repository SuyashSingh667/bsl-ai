from fastapi import APIRouter
from pydantic import BaseModel

from app.services import translation

router = APIRouter(prefix="/translate", tags=["translate"])


class TranslateRequest(BaseModel):
    text: str
    source_lang: str
    target_lang: str


class TranslateResponse(BaseModel):
    translated_text: str


@router.post("", response_model=TranslateResponse)
def translate(payload: TranslateRequest):
    if payload.target_lang == "en":
        result = translation.to_english(payload.text, payload.source_lang)
    elif payload.source_lang == "en":
        result = translation.from_english(payload.text, payload.target_lang)
    else:
        result = payload.text
    return TranslateResponse(translated_text=result)
