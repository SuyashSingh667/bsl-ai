"""
Translation between English and worker-spoken languages.

Intended implementation is AI4Bharat IndicTrans2 (see voice_pipeline.md),
but ai4bharat/indictrans2-*-dist-200M turned out to be a gated Hugging Face
repo — this session has no HF login/token to accept that license, so it's
a genuine access blocker, not a download flakiness issue like the earlier
Whisper/TTS substitutions. Meta's NLLB-200 was tried as an open alternative
but its download (~2.4GB) kept stalling on this network the same way
whisper-small and MMS-TTS did.

Using Helsinki-NLP's OPUS-MT models instead: smaller (~300MB) per-language-
pair models, ungated, and their downloads completed cleanly.

Known, tested quality limits of this substitute (not theoretical — observed
directly against real guidance text):
  - Short sentences (incident reports, verification answers) translate
    acceptably in both directions. This is the highest-stakes content,
    since it drives classification/routing/scoring, and it works.
  - Whole multi-paragraph markdown documents caused the model to degenerate
    into a repeating loop when translated in one call — fixed by
    translating line-by-line (see `_translate`).
  - "**bold**" markdown syntax specifically caused hallucinated/garbled
    output — fixed by stripping markdown emphasis before translating each
    line.
  - Specialized safety/technical vocabulary the model never saw in training
    ("flammable", "asphyxiant", section headers like "STOT") still produces
    garbled or partially-transliterated output even after both fixes above.
    This is a genuine capability ceiling of a small, general-domain,
    sentence-level model — not something more regex patching here will fix.
    IndicTrans2 (the originally intended model, blocked by gated HF access)
    or a domain glossary/pre-substitution pass are the real fixes; worth
    revisiting either once gated access is available.

Swapping the implementation later only touches this file;
`to_english`/`from_english` is the interface everything else calls.
"""

import functools
import os
import re

import torch
from transformers import MarianMTModel, MarianTokenizer

try:
    torch.set_num_threads(min(4, os.cpu_count() or 4))
except Exception:
    pass

_MARKDOWN_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")

_LANGUAGE_PAIR_MODELS = {
    ("hi", "en"): "Helsinki-NLP/opus-mt-hi-en",
    ("en", "hi"): "Helsinki-NLP/opus-mt-en-hi",
    ("bn", "en"): "Helsinki-NLP/opus-mt-bn-en",
    ("en", "bn"): "Helsinki-NLP/opus-mt-en-bn",
}

_MODEL_CACHE: dict[str, tuple[MarianMTModel, MarianTokenizer]] = {}

# Fast-path exact translation dictionary for sub-millisecond dispatch and interview answers
_EXACT_SAFETY_TRANSLATIONS: dict[str, str] = {
    "हाँ": "Yes",
    "हां": "Yes",
    "नहीं": "No",
    "नही": "No",
    "ना": "No",
    "पता नहीं": "Not sure / Unknown",
    "मालूम नहीं": "Unknown",
    "कोई नहीं": "No personnel",
    "कोई घायल नहीं": "No one injured",
    "कोई हताहत नहीं": "No casualties",
    "सभी सुरक्षित": "All workers safe",
    "सब सुरक्षित हैं": "All workers safe",
    "सुरक्षित": "Safe",
    "सुरक्षित है": "It is safe",
    "बंद कर दिया": "Shut down / Isolated",
    "बंद है": "Closed / Isolated",
    "आइसोलेट कर दिया": "Safely isolated",
    "वाल्व बंद है": "Valve closed",
    "गैस लीक": "Gas leak",
    "आग लगी है": "Fire has broken out",
    "धुआं निकल रहा है": "Smoke emitting",
    "खाली करा दिया": "Evacuated",
    "मशीन बंद है": "Machine stopped",
    "बिजली काट दी": "Power cut off",
    "बिजली बंद है": "Power is shut off",
    "मेन स्विच बंद": "Main breaker off",
}


_SAFETY_TERMS_TO_EN = {
    # Bengali
    "গ্যাস": "gas",
    "পাইপলাইন": "pipeline",
    "পাইপে": "pipeline",
    "ফুটো": "leak",
    "ছিদ্র": "leak",
    "নির্গমন": "leak escaping",
    "গন্ধ": "smell odor",
    "আগুন": "fire",
    "ধোঁয়া": "smoke",
    "ধোঁয়া": "smoke",
    "বিদ্যুৎ": "electrical",
    "শর্ট সার্কিট": "short circuit",
    "স্পার্ক": "spark",
    "রাসায়নিক": "chemical",
    "উপচে": "spill",
    "গলিত": "molten",
    "ধাতু": "metal",
    "ক্রেন": "crane",
    "পড়ে": "fall",
    "আহত": "injured",
    "বিস্ফোরণ": "explosion",
    "বড়": "big severe",
    # Tamil
    "வாயு": "gas",
    "குழாய்": "pipeline",
    "குழாயில்": "in pipeline",
    "கசிவு": "leak",
    "வாசனை": "smell odor",
    "தீ": "fire",
    "புகை": "smoke",
    "மின்சாரம்": "electrical",
    "தீப்பொறி": "spark",
    "காயம்": "injured hurt",
    "வேதிப்பொருள்": "chemical",
    "சிந்தியது": "spill",
    "உருகிய": "molten",
    "உலோகம்": "metal",
    "கிரேன்": "crane",
    "பெரிய": "big large severe",
    # Telugu
    "గ్యాస్": "gas",
    "పైపులైన్": "pipeline",
    "లీక్": "leak",
    "మంటలు": "fire",
    "పొగ": "smoke",
    "విద్యుత్": "electrical",
    "రసాయన": "chemical",
    "గాయం": "injury",
    "క్రేన్": "crane",
    "కరెంట్": "electrical",
    # Marathi
    "गॅस": "gas",
    "पाईपलाईन": "pipeline",
    "गळती": "leak",
    "आग": "fire",
    "धूर": "smoke",
    "विद्युत": "electrical",
    "शॉर्ट सर्किट": "short circuit",
    "इजा": "injury",
    "रासायनिक": "chemical",
    "क्रेन": "crane",
    "धोका": "danger hazard",
    # Gujarati
    "ગેસ": "gas",
    "પાઈપલાઈન": "pipeline",
    "લિકેજ": "leak",
    "આગ": "fire",
    "ધુમાડો": "smoke",
    "વીજળી": "electrical",
    "રસાયણ": "chemical",
    "ઈજા": "injury",
    "ક્રેન": "crane",
    # Kannada
    "ಅನಿಲ": "gas",
    "ಪೈಪ್‌ಲೈನ್": "pipeline",
    "ಸೋರಿಕೆ": "leak",
    "ಬೆಂಕಿ": "fire",
    "ಹೊಗೆ": "smoke",
    "ವಿದ್ಯುತ್": "electrical",
    "ರಾಸಾಯನಿಕ": "chemical",
    "ಗಾಯ": "injury",
    "ಕ್ರೇನ್": "crane",
    # Malayalam
    "വാതകം": "gas",
    "പൈപ്പ്‌ലൈൻ": "pipeline",
    "ചോർച്ച": "leak",
    "തീ": "fire",
    "പുക": "smoke",
    "വൈദ്യുതി": "electrical",
    "രാസവസ്തു": "chemical",
    "പരിക്ക്": "injury",
    "ക്രെയിൻ": "crane",
    # Punjabi
    "ਗੈਸ": "gas",
    "ਪਾਈਪਲਾਈਨ": "pipeline",
    "ਲੀਕੇਜ": "leak",
    "ਅੱਗ": "fire",
    "ਧੂੰਆਂ": "smoke",
    "ਬਿਜਲੀ": "electrical",
    "ਰਸਾਇਣ": "chemical",
    "ਸੱਟ": "injury",
    "ਕ੍ਰੇਨ": "crane",
    # Odia
    "ଗ୍ୟାସ": "gas",
    "ପାଇପଲାଇନ": "pipeline",
    "ଲିକେଜ": "leak",
    "ନିଆଁ": "fire",
    "ଧୂଆଁ": "smoke",
    "ବିଦ୍ୟୁତ": "electrical",
    "ରାସାୟନିକ": "chemical",
    "ଆଘାତ": "injury",
    "କ୍ରେନ": "crane",
    # Hindi
    "आग": "fire",
    "अग्नि": "fire",
    "धुआं": "smoke",
    "धुआँ": "smoke",
    "लपटें": "flames",
    "जल रहा": "burning",
    "ट्रक": "truck",
    "तरक": "truck",
    "डंपर": "dumper truck",
    "शॉर्ट सर्किट": "short circuit",
    "सर्किट": "electrical circuit",
    "झटका": "electric shock",
    "बिजली का झटका": "electric shock electrocution",
    "विद्युत": "electrical",
    "बिजली": "electrical power",
    "करंट": "electrical current",
    "लाइव वायर": "live wire",
    "बिजली का तार": "live electrical cable",
    "मेन स्विच": "main electrical breaker",
    "दस लोग": "10 workers",
    "पांच लोग": "5 workers",
    "धुआं फैल": "rapid smoke spread",
    "गैस": "gas",
    "रिसाव": "leak",
    "लीक": "leak",
    "बदबू": "foul odor",
    "गंध": "smell",
    "ब्लास्ट फर्नेस": "blast furnace",
    "कोक ओवन": "coke oven",
    "पिघला हुआ": "molten",
    "पिघला लोहा": "molten metal",
    "लैडल": "ladle",
    "क्रेन": "crane",
    "तार टूटा": "wire rope snapped",
    "हुक": "crane hook",
    "एसिड": "acid",
    "तेजाब": "acid chemical",
    "फिसल": "slip",
    "गिर पड़ा": "fell down",
    "चोट": "injury",
    "बेहोश": "unconscious",
    "सीमित स्थान": "confined space",
    "पीपीई": "PPE",
    "हेलमेट": "helmet",
    "दस्ताने": "gloves",
}


def _get_model(source_lang: str, target_lang: str) -> tuple[MarianMTModel, MarianTokenizer] | None:
    checkpoint = _LANGUAGE_PAIR_MODELS.get((source_lang, target_lang))
    if not checkpoint:
        return None
    if checkpoint not in _MODEL_CACHE:
        try:
            tokenizer = MarianTokenizer.from_pretrained(checkpoint, local_files_only=True)
            model = MarianMTModel.from_pretrained(checkpoint, local_files_only=True)
            _MODEL_CACHE[checkpoint] = (model, tokenizer)
        except Exception:
            try:
                tokenizer = MarianTokenizer.from_pretrained(checkpoint)
                model = MarianMTModel.from_pretrained(checkpoint)
                _MODEL_CACHE[checkpoint] = (model, tokenizer)
            except Exception:
                return None
    return _MODEL_CACHE.get(checkpoint)


def _translate_line(text: str, model: MarianMTModel, tokenizer: MarianTokenizer) -> str:
    with torch.inference_mode():
        inputs = tokenizer([text], return_tensors="pt", padding=True, truncation=True)
        translated = model.generate(**inputs, max_new_tokens=64, num_beams=1)
        return tokenizer.decode(translated[0], skip_special_tokens=True)


def _dictionary_fallback(text: str) -> str:
    translated = text
    matches = []
    for term, en in _SAFETY_TERMS_TO_EN.items():
        if term in text:
            matches.append(en)
    if matches:
        return f"{' '.join(matches)} ({text})"
    return text


def _translate(text: str, source_lang: str, target_lang: str) -> str:
    if source_lang == target_lang or not text.strip():
        return text

    pair = _get_model(source_lang, target_lang)
    if pair is None:
        if target_lang == "en":
            return _dictionary_fallback(text)
        return text

    model, tokenizer = pair

    # Short single sentence translation fast-path: avoids multiline overhead
    clean_text = text.strip()
    if "\n" not in clean_text:
        clean_line = _MARKDOWN_BOLD_RE.sub(r"\1", clean_text)
        return _translate_line(clean_line, model, tokenizer)

    lines = text.split("\n")
    translated_lines = []
    for line in lines:
        if not line.strip():
            translated_lines.append(line)
            continue
        clean_line = _MARKDOWN_BOLD_RE.sub(r"\1", line)
        translated_lines.append(_translate_line(clean_line, model, tokenizer))
    return "\n".join(translated_lines)


@functools.lru_cache(maxsize=4096)
def to_english(text: str, source_lang: str) -> str:
    stripped = text.strip()
    # 1. Fast-path exact safety dictionary check (sub-millisecond return)
    if stripped in _EXACT_SAFETY_TRANSLATIONS:
        return _EXACT_SAFETY_TRANSLATIONS[stripped]

    res = _translate(text, source_lang, "en")
    # Post-translation safety domain normalizations (correcting MarianMT literal translation misses)
    res = re.sub(r"\bpower\s+blow\b", "electric shock", res, flags=re.IGNORECASE)
    res = re.sub(r"\bblow\s+of\s+power\b", "electric shock", res, flags=re.IGNORECASE)
    res = re.sub(r"\bblow\s+of\s+electricity\b", "electric shock", res, flags=re.IGNORECASE)
    res = re.sub(r"\blife\s+wire\b", "live wire", res, flags=re.IGNORECASE)
    if "बिजली" in text or "झटका" in text or "करंट" in text:
        if "shock" not in res.lower() and "electric" not in res.lower():
            res = f"{res} (electric shock hazard)"
    if "क्रेन" in text and "crane" not in res.lower():
        res = f"{res} (overhead crane)"
    if "आग" in text and "fire" not in res.lower():
        res = f"{res} (fire hazard)"
    return res


@functools.lru_cache(maxsize=4096)
def from_english(text: str, target_lang: str) -> str:
    return _translate(text, "en", target_lang)


def is_supported(language: str) -> bool:
    return language == "en" or ("en", language) in _LANGUAGE_PAIR_MODELS

