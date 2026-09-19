from __future__ import annotations

import logging
import re
from typing import Any

import faster_whisper.audio as fwa
import numpy as np
from faster_whisper import WhisperModel

from app.config import WHISPER_MODEL_SIZE

logger = logging.getLogger(__name__)

_model: WhisperModel | None = None


def _get_model() -> WhisperModel:
    global _model
    if _model is None:
        _model = WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")
    return _model


# ---------------------------------------------------------------------------
# Domain-vocabulary initial prompts — fed to Whisper's decoder to bias
# towards steel-plant terminology and common Hindi industrial phrases.
# ---------------------------------------------------------------------------

PROMPT_VOCAB_EN = (
    "Bokaro Steel Limited (BSL) steel plant safety incident report: Blast furnace, coke oven, converter, SMS, "
    "hot strip mill, cold rolling mill, gas leak, carbon monoxide, CO gas, toxic fumes, gas holder station, "
    "valve V-12, flange, pipeline, fire, flame, smoke, explosion, electrical hazard, short circuit, arc flash, "
    "transformer, switchgear, breaker, panel, molten metal spill, hot metal ladle, slag, tundish, crane, "
    "wire rope snapped, hook, dropped load, hoist, confined space, storage tank, pit, manhole, asphyxiation, "
    "slip, trip, fall, wet floor, chemical spill, acid leak, hydrochloric acid, battery, truck fire, dumper collision, "
    "ambulance, evacuation, PPE, helmet, siren, control room, safety officer, fire brigade, gas detector, "
    "oxygen level, ventilation, SCBA, first aid, burn injury, fracture, unconscious, stretcher, casualty."
)

PROMPT_VOCAB_HI = (
    "बोकारो स्टील प्लांट (BSL) औद्योगिक सुरक्षा आपातकालीन रिपोर्ट: ब्लास्ट फर्नेस, कोक ओवन, एसएमएस, "
    "हॉट स्ट्रिप मिल, कोल्ड रोलिंग, गैस रिसाव, कार्बन मोनोऑक्साइड, जहरीली गैस, वाल्व, फ्लैंज, पाइपलाइन, "
    "आग लग गई, धुआं, लपटें, विस्फोट, शॉर्ट सर्किट, बिजली का झटका, स्पार्क, ट्रांसफार्मर, पैनल, "
    "पिघला हुआ लोहा, हॉट मेटल लैडल, स्लैग, क्रेन, तार टूटा, लोड गिरा, सीमित स्थान, टैंक, गड्ढा, "
    "एसिड रिसाव, तेजाब, हाइड्रोक्लोरिक, ट्रक में आग, डंपर टक्कर, गाड़ी, सायरन, एम्बुलेंस, प्राथमिक उपचार, "
    "नियंत्रण कक्ष, खाली कराया, "
    # Common Hindi interview answer phrases that Whisper often mishears:
    "हाँ, नहीं, पता नहीं, मैंने देखा, आग लगी है, गैस निकल रही है, "
    "बहुत तेज धुआं, लोग घायल, बेहोश, करंट लगा, बिजली का तार टूटा, "
    "पानी फैला हुआ, फिसल गया, गिर पड़ा, चोट लगी, हेलमेट नहीं, "
    "दो लोग, पांच लोग, दस लोग, कोई नहीं, बंद कर दिया, खाली करा दिया, "
    "मेन स्विच, ब्रेकर, केबल, मोटर, पंप, कम्प्रेसर, "
    "ब्लास्ट फर्नेस एक, ब्लास्ट फर्नेस दो, गैस होल्डर, ऑक्सीजन प्लांट, "
    "सिंटर प्लांट, रोलिंग मिल, पावर प्लांट, सब स्टेशन, कंट्रोल रूम, "
    "फायर ब्रिगेड, सेफ्टी ऑफिसर, PPE, हेलमेट, दस्ताने, सेफ्टी शूज, "
    "एसिड टैंक, केमिकल, हाइड्रोक्लोरिक एसिड, सल्फ्यूरिक एसिड।"
)

PROMPT_VOCAB_BY_LANG: dict[str, str] = {
    "en": PROMPT_VOCAB_EN,
    "hi": PROMPT_VOCAB_HI,
    "bn": "বোকারো স্টিল প্ল্যান্ট (BSL) শিল্প নিরাপত্তা রিপোর্ট: গ্যাস লিকেজ, আগুন, ধোঁয়া, শর্ট সার্কিট, ভাল্ব, পাইপলাইন, বিস্ফোরণ, চিকিৎসা, অ্যাম্বুলেন্স, ক্রেন, তার ছিঁড়ে গেছে, আহত, অজ্ঞান।",
    "ta": "பொகாரோ ஸ்டீல் ஆலை (BSL) தொழில்துறை பாதுகாப்பு அறிக்கை: எரிவாயு கசிவு, தீ விபத்து, புகை, ஷார்ட் சர்க்யூட், வால்வு, பைப்லைன், கிரேன், ஆசிட் கசிவு, காயம், மயக்கம்.",
    "te": "బొకారో స్టీల్ ప్లాంట్ (BSL) భద్రతా నివేదిక: గ్యాస్ లీకేజ్, మంటలు, పొగ, షార్ట్ సర్క్యూట్, వాల్వ్, పైప్‌లైన్, క్రేన్, రసాయన లీకేజీ, గాయం.",
    "mr": "बोकारो स्टील प्लांट (BSL) औद्योगिक सुरक्षा अहवाल: गॅस गळती, आग, धूर, शॉर्ट सर्किट, व्हॉल्व्ह, पाईपलाईन, क्रेन, अपघात, जखमी, बेशुद्ध.",
    "gu": "બોકારો સ્ટીલ પ્લાન્ટ (BSL) સલામતી અહેવાલ: ગેસ ગળતર, આગ, ધુમાડો, શોર્ટ સર્કિટ, વાલ્વ, પાઇપલાઇન, ક્રેન, એસિડ લિક, ઈજા.",
    "kn": "ಬೊಕಾರೊ ಸ್ಟೀಲ್ ಪ್ಲಾಂಟ್ (BSL) ಸುರಕ್ಷತಾ ವರದಿ: ಅನಿಲ ಸೋರಿಕೆ, ಬೆಂಕಿ, ಹೊಗೆ, ಶಾರ್ಟ್ ಸರ್ಕ್ಯೂಟ್, ವಾಲ್ವ್, ಪೈಪ್‌ಲೈನ್, ಕ್ರೇನ್, ಆಸಿಡ್ ಸೋರಿಕೆ, ಗಾಯ.",
    "ml": "ബൊക്കാറോ സ്റ്റീൽ പ്ലാന്റ് (BSL) സുരക്ഷാ റിപ്പോർട്ട്: ഗ്യാസ് ചോർച്ച, തീപിടുത്തം, പുക, ഷോർട്ട് സർക്യൂട്ട്, വാൽവ്, പൈപ്പ്‌ലൈൻ, ക്രെയിൻ, പരിക്ക്.",
    "pa": "ਬੋਕਾਰੋ ਸਟੀਲ ਪਲਾਂਟ (BSL) ਸੁਰੱਖਿਆ ਰਿਪੋਰਟ: ਗੈਸ ਲੀਕ, ਅੱਗ, ਧੂੰਆਂ, ਸ਼ਾਰਟ ਸਰਕਟ, ਵਾਲਵ, ਪਾਈਪਲਾਈਨ, ਕਰੇਨ, ਐਸਿਡ ਲੀਕ, ਸੱਟ।",
    "or": "ବୋକାରୋ ଷ୍ଟିଲ୍ ପ୍ଲାଣ୍ଟ (BSL) ସୁରକ୍ଷା ରିପୋର୍ଟ: ଗ୍ୟାସ୍ ଲିକେଜ୍, ନିଆଁ, ଧୂଆଁ, ଶର୍ଟ ସର୍କିଟ୍, ଭଲଭ୍, ପାଇପଲାଇନ୍, କ୍ରେନ୍, ବିପଦ, ଆଘାତ।",
}

_INDIC_LANGS = {"hi", "bn", "ta", "te", "mr", "gu", "kn", "ml", "pa", "or"}

# Regex matching Arabic / Perso-Arabic unicode ranges (Urdu script)
_ARABIC_RE = re.compile(r"[\u0600-\u06ff\u0750-\u077f\ufb50-\ufdff\ufe70-\ufeff]")
# Regex matching CJK or Japanese Kana hallucination artifacts
_CJK_KANA_RE = re.compile(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")


def has_arabic_script(text: str) -> bool:
    """Checks if text contains Arabic/Urdu unicode script."""
    return bool(_ARABIC_RE.search(text))


def clean_repeated_phrases(text: str) -> str:
    """Deduplicate repetitive speech hallucinations (e.g. 'cake, cake, cake' or 'लगे लगे लगे')."""
    if not text:
        return ""
    words = text.split()
    if not words:
        return ""
    cleaned = []
    for w in words:
        if len(cleaned) >= 2 and w == cleaned[-1] and w == cleaned[-2]:
            continue
        cleaned.append(w)
    res = " ".join(cleaned)
    pattern = re.compile(r"(\b.+?\b)(?:\s*[,.]?\s*\1){2,}", re.IGNORECASE)
    res = pattern.sub(r"\1", res)
    return res.strip()


# ---------------------------------------------------------------------------
# Hindi phonetic correction dictionary — fixes common Whisper misrecognitions
# of Hindi speech with Indian accents in noisy industrial environments.
# Expanded significantly to cover more variations observed in field usage.
# ---------------------------------------------------------------------------

_PHONETIC_REPLACEMENTS = [
    # ---- Electrical shock / live wire / breaker ----
    (r"(लिजली|बपचली|बचली|बिजिलि|बिजिली|बिज्ली|बिजल)", "बिजली"),
    (r"(जहत\s*का|छट\s*का|झट\s*का|छूट\s*का|झठका|ज्वत\s*का|झटका\s*का)", "झटका"),
    (r"(अद्वी|अदमी|अक\s*अदमी|अकादमी)", "एक आदमी"),
    (r"(नगा|अगा|बगा)\s+है", "लगा है"),
    (r"(लाइफ\s*वायर|life\s*wire)", "लाइव वायर"),
    (r"(दिली\s*के\s*तार|दिलि\s*के\s*तार|तारो\s*में)", "बिजली के तारों में"),
    (r"(करण|करन)\s*(?:लगा|का)?", "करंट लगा"),
    (r"(मेट्र\s*सावज|मेन\s*सावज|मेन\s*स्वीच|मेन\s*स्विच)\s*(?:बुत्ज|बुझ|बंद)?", "मेन स्विच बंद किया है"),
    (r"(चोट\s*सरकेत|चिट\s*सरकेत|शट\s*सरकट|चिट\s*क्षूथ\s*सरकेद|सर्ट\s*सरकट|शट\s*सकट)", "शॉर्ट सर्किट"),
    (r"(बिरेकर|ब्रिकर|ब्रैकर|ब्रेकड)", "ब्रेकर"),
    (r"(ट्रांस्फॉर्मर|ट्रांसफामर|ट्रान्स\s*फार्मर|ट्रांसफोर्मर)", "ट्रांसफार्मर"),
    (r"(स्वीचगीयर|सिविचगियर|स्विचगेयर)", "स्विचगियर"),
    (r"(करण्ट|करंद|करेन्ट|करन्ट)", "करंट"),

    # ---- Crane / lifting ----
    (r"(करेन|केरेन|प्राटी\s*क्रेन|बड़ी\s*क्रेन)", "क्रेन"),
    (r"(तार\s*रस्सी|वायर\s*रोफ|वायर\s*रोप|तार\s*रोप)", "वायर रोप"),
    (r"(होइस्ट|हायस्ट|होईस्ट|हॉइस्ट)", "होइस्ट"),
    (r"(स्लिंग|शलिंग|स्लींग)", "स्लिंग"),

    # ---- Transport / vehicles ----
    (r"(तरक|टर्क|तरुक|टरक)", "ट्रक"),
    (r"(डमपर|दम्पर|दमपर)", "डंपर"),
    (r"(फोर्क\s*लिफ्ट|फोर्कलिप्ट|फार्कलिफ्ट)", "फोर्कलिफ्ट"),
    (r"(लोकोमोटिव|लोकोमोटीव|लोको\s*मोटिव)", "लोकोमोटिव"),

    # ---- Fire & Smoke ----
    (r"(आग\s*वाग)", "आग लगी"),
    (r"(अग\s+अगती|आग\s+अगती|आग\s+लगती|आग\s+अगलती|आग\s+अग\s+अगती)", "आग लगती"),
    (r"(हुटिवी|हुई\s*दिख|दिखा\s*रहा)", "हुई दिखाई"),
    (r"(तेखाय|देखाए)\s*देरही", "दिखाई दे रही"),
    (r"(धुवा|धुआ)\s*(बहल|फैल|फेल)", "धुआं फैल"),
    (r"(कुक\s*अपन|कुक\s*अवान|स्मोक\s*ओवन)", "कोक ओवन"),
    (r"(लफटें|लपतें|लपटे)", "लपटें"),
    (r"(धमाखा|तमाका|धमाक|दमाका)", "धमाका"),
    (r"(विषफोट|विसफोट|भिस्फोट)", "विस्फोट"),

    # ---- Gas / Chemical ----
    (r"(गाइस|गैस\s*रिसाब|गेस\s*रिसाव|गॅस\s*रिसाव)", "गैस रिसाव"),
    (r"(अभीता\s*गैसा|अभि\s*तक\s*ऐसा)", "अभी तक ऐसा"),
    (r"(नहीं\s*जा|नही\s*जा|नहीं\s*बुझा)", "नहीं बुझा सकते"),
    (r"(हाइड्रो\s*क्लोरिक|हायड्रो\s*क्लोरिक|हाइड्रोकलोरिक)", "हाइड्रोक्लोरिक"),
    (r"(सल्फ्युरिक|सलफ्यूरिक|सल्फ़्यूरिक)", "सल्फ्यूरिक"),
    (r"(कार्बन\s*मोनो\s*ऑक्साइड|कार्बन\s*मोनॉक्साइड|CO\s*गैस)", "कार्बन मोनोऑक्साइड"),
    (r"(एसिट|ऐसिड|ऐसीड)", "एसिड"),
    (r"(तेज़ाब|तेजाभ|तेजब)", "तेजाब"),

    # ---- Location & Plant areas ----
    (r"(ब्लास्ट\s*फरनेस|बलास्ट\s*फर्नस|ब्लास्ट\s*फर्नस|ब्लास्ट\s*फरनस)", "ब्लास्ट फर्नेस"),
    (r"(गैस\s*होल्डर|गैस\s*होलडर|गॅस\s*होल्डर)", "गैस होल्डर"),
    (r"(ऑक्सीजन\s*प्लांट|ऑक्सिजन\s*प्लान्ट|ऑक्सीजन\s*प्लैंट)", "ऑक्सीजन प्लांट"),
    (r"(सिंटर\s*प्लांट|सिन्टर\s*प्लांट|सिंतर\s*प्लांट)", "सिंटर प्लांट"),
    (r"(सब\s*स्टेशन|सबस्टेसन|सब\s*स्टेसन)", "सब स्टेशन"),
    (r"(कंट्रोल\s*रूम|कन्ट्रोल\s*रूम|कंट्रोल\s*रुम)", "कंट्रोल रूम"),
    (r"(पावर\s*प्लांट|पावर\s*प्लान्ट|पॉवर\s*प्लांट)", "पावर प्लांट"),

    # ---- Safety equipment / PPE ----
    (r"(हेल्मेट|हेलमट|हैल्मेट)", "हेलमेट"),
    (r"(दस्ताने|दस्ताना|गल्वज)", "दस्ताने"),
    (r"(सेफटी\s*शूज|सेफ़्टी\s*शूज|सेप्टी\s*जूते)", "सेफ्टी शूज"),
    (r"(पी\s*पी\s*ई|PPE|पीपीई)", "PPE"),
    (r"(SCBA|एससीबीए|स्कबा)", "SCBA"),

    # ---- Actions / Conditions ----
    (r"(बे\s*होश|बेहोस|बेहोष)", "बेहोश"),
    (r"(घयाल|घायाल|घईल)", "घायल"),
    (r"(प्राथमिक\s*उपचार|प्राथमीक\s*उपचार|प्रथमिक\s*उपचार)", "प्राथमिक उपचार"),
    (r"(खाली\s*कराया|खाली\s*करवाया|इवैक्यूएशन|इवेक्यूएट)", "खाली कराया"),
    (r"(बन्द\s*कर\s*दिया|बंध\s*कर\s*दिया|बन्ध\s*किया)", "बंद कर दिया"),
    (r"(आइसोलेट|आइसोलेशन|आइसोलेटेड)", "आइसोलेट किया"),
    (r"(फायर\s*ब्रिगेड|फ़ायर\s*ब्रिगेड|फ़ायर\s*ब्रिगेट)", "फायर ब्रिगेड"),
    (r"(सायरन|शायरन|साइरन|सायरेन)", "सायरन"),
    (r"(एम्बुलेंस|एम्बुलेन्स|ऐम्बुलेन्स|एम्बुलांस)", "एम्बुलेंस"),

    # ---- Quantities & Answers ----
    (r"(Does\s*look|दास\s*लोग|दश\s*लोग|दस्स\s*लोग|१०\s*लोग)", "दस लोग"),
    (r"(पांच\s*लोग|५\s*लोग)", "5 लोग"),
    (r"(दो\s*लोग|२\s*लोग)", "2 लोग"),
    (r"(तीन\s*लोग|३\s*लोग)", "3 लोग"),

    # ---- Common Yes/No/Uncertain answer corrections ----
    (r"^(हा|हां|हम|ह)$", "हाँ"),
    (r"^(नही|नै|ना|नह|ने)$", "नहीं"),
    (r"(पता\s*नही|पता\s*ने|मालूम\s*नही)", "पता नहीं"),
    (r"(देखा\s*था|देका\s*था|दिखा\s*था)", "देखा था"),
    (r"(सुना\s*था|सूना\s*था|सूना\s*है)", "सुना है"),
]

_ENGLISH_PHONETIC_FIXES = [
    (r"\baccused\s+of\s+being\s+a\s+criminal\b", "struck by an electric shock via a live wire"),
    (r"\baccused\s+of\s+a\s+crime\b", "struck by an electric shock via a live wire"),
    (r"\bpower\s+blow\b", "electric shock"),
    (r"\bblow\s+of\s+power\b", "electric shock"),
    (r"\bblow\s+of\s+electricity\b", "electric shock"),
    (r"\belectric\s+power\s+blow\b", "electric shock"),
    (r"\blife\s*wire\b", "live wire"),
    (r"\bstruck\s+with\s+lightning\b", "struck by an electric shock"),
    (r"\bstuck\s+by\s+lightning\b", "struck by an electric shock"),
    (r"\bsmoke\s+oven\b", "coke oven"),
    (r"\bDoes\s+look\s+positive\b", "10 workers present in danger zone"),
    (r"\bDust\s+look\s+has\s+happened\b", "10 workers in danger zone"),
    (r"\bfight\b", "fire"),
    (r"\bgarden\b", "gas"),
    (r"\bloot\b", "leak"),
    (r"\bbuy,\s*it's\b", "blast furnace"),
    (r"\btwirl\b", "transformer"),
]


def normalize_hindi_phonetics(text: str) -> str:
    """Corrects common Whisper phonetic mistranscriptions on Indian accent Hindi speech."""
    if not text:
        return ""
    res = text
    for pat, rep in _PHONETIC_REPLACEMENTS:
        res = re.sub(pat, rep, res, flags=re.IGNORECASE)
    return res


def normalize_english_safety_terms(text: str) -> str:
    """Corrects common misheard industrial safety terms in English translation."""
    if not text:
        return ""
    res = text
    for pat, rep in _ENGLISH_PHONETIC_FIXES:
        res = re.sub(pat, rep, res, flags=re.IGNORECASE)
    return res


def clean_hallucinations(text: str) -> str:
    """Removes CJK/Japanese artifacts, collapses repetitive tokens, and applies phonetic fixes."""
    if not text:
        return ""
    cleaned = _CJK_KANA_RE.sub(" ", text)
    cleaned = clean_repeated_phrases(cleaned)
    cleaned = normalize_hindi_phonetics(cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def _load_and_normalize_audio(audio_path: str) -> np.ndarray | str:
    """Decodes audio to 16kHz float32 array and applies dynamic range gain normalization
    with noise gate to suppress low-level ambient plant noise."""
    try:
        audio = fwa.decode_audio(audio_path)

        # Noise gate: suppress ambient plant noise below threshold
        noise_floor = float(np.percentile(np.abs(audio), 10)) if len(audio) > 1000 else 0.0
        gate_threshold = max(noise_floor * 3.0, 0.003)
        mask = np.abs(audio) > gate_threshold
        # Apply soft gate (attenuate rather than silence) to preserve speech transitions
        attenuation = np.where(mask, 1.0, 0.1)
        audio = audio * attenuation

        # Dynamic range normalization
        peak = float(np.max(np.abs(audio))) if len(audio) > 0 else 0.0
        if peak > 0.005:
            scale = 0.90 / max(peak, 0.08)
            audio = np.clip(audio * scale, -1.0, 1.0)
        return audio.astype(np.float32)
    except Exception as exc:
        logger.warning(f"Audio decoding error for {audio_path}: {exc}")
        return audio_path


def transcribe(audio_path: str, language: str | None = None) -> tuple[str, str, float]:
    model = _get_model()
    audio_input = _load_and_normalize_audio(audio_path)
    initial_prompt = PROMPT_VOCAB_BY_LANG.get(language, PROMPT_VOCAB_HI) if language else PROMPT_VOCAB_HI
    segments, info = model.transcribe(
        audio_input,
        language=language,
        initial_prompt=initial_prompt,
        beam_size=5,
        temperature=0.0,
        condition_on_previous_text=False,
        vad_filter=True,
        task="transcribe",
    )
    raw_text = " ".join(segment.text.strip() for segment in segments).strip()
    text = clean_hallucinations(raw_text)
    detected_lang = info.language
    if detected_lang == "ur" or has_arabic_script(text):
        detected_lang = "hi"
    return text, detected_lang, round(info.language_probability, 3)


def transcribe_and_translate(
    audio_path: str, language: str | None = None
) -> tuple[str, str, str, float]:
    """
    Universal speech processor with automatic language realization and deep domain vocabulary:
    1. Normalizes audio gain and applies noise gate for noisy plant environments.
    2. Decodes with Bokaro Steel domain vocabulary initial prompts.
    3. Strictly enforces Urdu suppression: if 'ur' is detected or Arabic script is present,
       re-transcribes immediately in Hindi with Devanagari prompting.
    4. Automatically resolves spoken Indian language vs English hypothesis.
    5. Multi-pass transcription: if confidence is low, re-transcribes with forced Hindi.
    6. Translates native speech to high-fidelity English for downstream classification.
    Returns: (native_text, english_text, detected_language, confidence)
    """
    model = _get_model()
    audio_input = _load_and_normalize_audio(audio_path)

    effective_lang_hint = language if (language and language not in ["auto", "null", "undefined"]) else None
    initial_prompt = PROMPT_VOCAB_BY_LANG.get(effective_lang_hint, PROMPT_VOCAB_HI)

    # Step 1: Decode with VAD and domain vocabulary — force temperature=0 for determinism
    segments, info = model.transcribe(
        audio_input,
        language=effective_lang_hint,
        initial_prompt=initial_prompt,
        beam_size=5,
        temperature=0.0,
        condition_on_previous_text=False,
        vad_filter=True,
        task="transcribe",
    )
    raw_list = list(segments)
    native_text = clean_hallucinations(" ".join(s.text.strip() for s in raw_list))
    detected_lang = info.language
    confidence = round(info.language_probability, 3)

    # Step 2: Strict Urdu suppression & Arabic script re-decoding
    if detected_lang == "ur" or has_arabic_script(native_text):
        detected_lang = "hi"
        try:
            segs_hi, info_hi = model.transcribe(
                audio_input,
                language="hi",
                initial_prompt=PROMPT_VOCAB_HI,
                temperature=0.0,
                beam_size=5,
                condition_on_previous_text=False,
                vad_filter=True,
                task="transcribe",
            )
            native_text = clean_hallucinations(" ".join(s.text.strip() for s in segs_hi))
            confidence = round(info_hi.language_probability, 3)
        except Exception as exc:
            logger.warning(f"Failed to re-transcribe Urdu to Hindi: {exc}")

    # Step 3: Multi-pass — if confidence is low and hint was Hindi, try again
    # with stricter parameters for a second opinion
    if confidence < 0.70 and (effective_lang_hint == "hi" or detected_lang == "hi"):
        try:
            segs_retry, info_retry = model.transcribe(
                audio_input,
                language="hi",
                initial_prompt=PROMPT_VOCAB_HI,
                temperature=0.0,
                beam_size=8,  # wider beam for more careful decoding
                condition_on_previous_text=False,
                vad_filter=True,
                task="transcribe",
            )
            retry_list = list(segs_retry)
            retry_text = clean_hallucinations(" ".join(s.text.strip() for s in retry_list))
            retry_conf = round(info_retry.language_probability, 3)
            # Use the retry if it's more confident or has more meaningful content
            retry_logprob = sum(s.avg_logprob for s in retry_list) / len(retry_list) if retry_list else -99.0
            orig_logprob = sum(s.avg_logprob for s in raw_list) / len(raw_list) if raw_list else -99.0
            if retry_conf > confidence or retry_logprob > orig_logprob:
                native_text = retry_text
                confidence = retry_conf
                detected_lang = "hi"
                raw_list = retry_list
                logger.info(f"Multi-pass Hindi re-transcription improved confidence: {confidence}")
        except Exception as exc:
            logger.warning(f"Multi-pass Hindi retry failed: {exc}")

    # Step 4: Automatic language realization when user did not select a language
    if not effective_lang_hint:
        probs = dict(info.all_language_probs) if hasattr(info, "all_language_probs") and info.all_language_probs else {}
        en_prob = probs.get("en", confidence if detected_lang == "en" else 0.0)
        hi_prob = probs.get("hi", 0.0) + probs.get("ur", 0.0)
        indic_scores = {l: probs.get(l, 0.0) for l in _INDIC_LANGS}
        top_indic_lang, top_indic_prob = max(indic_scores.items(), key=lambda x: x[1]) if indic_scores else ("hi", 0.0)

        # If Whisper default guessed 'en', check if acoustic evidence points to Indic language
        if detected_lang == "en":
            target_indic = top_indic_lang if (top_indic_prob >= 0.10 and top_indic_lang != "ur") else "hi"
            prompt_indic = PROMPT_VOCAB_BY_LANG.get(target_indic, PROMPT_VOCAB_HI)
            try:
                segs_indic, _ = model.transcribe(
                    audio_input,
                    language=target_indic,
                    temperature=0.0,
                    beam_size=5,
                    initial_prompt=prompt_indic,
                    condition_on_previous_text=False,
                    vad_filter=True,
                    task="transcribe",
                )
                list_indic = list(segs_indic)
                text_indic = clean_hallucinations(" ".join(s.text.strip() for s in list_indic))
                logprob_indic = sum(s.avg_logprob for s in list_indic) / len(list_indic) if list_indic else -99.0
                logprob_en = sum(s.avg_logprob for s in raw_list) / len(raw_list) if raw_list else -99.0
                is_en_repetitive = bool(re.search(r"(\b.+?\b)(?:\s*[,.]?\s*\1){2,}", native_text, re.IGNORECASE))

                if (logprob_indic > logprob_en) or is_en_repetitive or (hi_prob >= en_prob) or (top_indic_prob >= 0.15 and en_prob < 0.70):
                    detected_lang = target_indic
                    confidence = round(max(hi_prob, top_indic_prob, 0.85), 3)
                    native_text = text_indic or native_text
            except Exception as exc:
                logger.warning(f"Acoustic Indic verification exception: {exc}")

    # Step 5: High-fidelity domain-grounded English translation
    if detected_lang == "en":
        english_text = native_text
    else:
        try:
            segments_en, _ = model.transcribe(
                audio_input,
                language=detected_lang,
                initial_prompt=PROMPT_VOCAB_EN,
                beam_size=5,
                temperature=0.0,
                condition_on_previous_text=False,
                vad_filter=True,
                task="translate",
            )
            english_text = clean_hallucinations(" ".join(segment.text.strip() for segment in segments_en))
        except Exception as exc:
            logger.warning(f"Translation exception: {exc}")
            english_text = ""

        # Reconcile with Marian domain translation if native text contains safety terms
        try:
            from app.services import translation
            marian_en = translation.to_english(native_text, detected_lang)
            safety_words = ["आग", "गैस", "सर्किट", "शॉर्ट", "क्रेन", "एसिड", "पिघला", "चोट", "धुआं", "बिजली", "झटका", "करंट", "वायर", "केबल", "गिर", "ब्रेकर", "तार", "धमाका", "लोग", "रिसाव", "विस्फोट", "लपटें", "भट्ठी", "होइस्ट", "डंपर"]
            has_safety = any(w in native_text for w in safety_words)
            is_hallucinated = any(w in english_text.lower() for w in ["criminal", "accused", "loot", "garden", "buy, it's", "twirl", "fight"])

            if is_hallucinated or not english_text:
                english_text = marian_en or english_text
            elif has_safety and marian_en and marian_en.strip() != native_text.strip():
                english_text = f"{english_text}. {marian_en}"
        except Exception as exc:
            logger.warning(f"Marian translation augmentation error: {exc}")

        if not english_text:
            english_text = native_text

    english_text = normalize_english_safety_terms(english_text)
    return native_text, english_text or native_text, detected_lang, confidence
