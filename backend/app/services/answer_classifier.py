"""
Answer Identification & Information Extraction Model.
Uses zero-shot semantic embedding projections and pattern recognition
to extract structured safety facts from worker verification answers.
"""

import re
from typing import Any
from app.services import embeddings

_EQUIPMENT_KEYWORDS = {
    "valve": ["valve", "cock", "stopcock", "valv", "वाल्व", "वाल"],
    "flange": ["flange", "joint", "gasket", "coupling", "फ्लैंज", "जोड़"],
    "pipeline": ["pipe", "pipeline", "line", "conduit", "manifold", "पाइप", "पाइपलाइन"],
    "storage_tank": ["tank", "gasholder", "holder", "vessel", "cylinder", "silo", "टैंक", "गैस होल्डर", "सिलेंडर"],
    "furnace": ["furnace", "blast furnace", "coke oven", "converter", "tundish", "भट्ठी", "ब्लास्ट फर्नेस", "कोक ओवन", "कनवर्टर", "टंडिश"],
    "pump_compressor": ["pump", "compressor", "blower", "fan", "पंप", "कंप्रेसर", "ब्लोअर"],
    "electrical": ["cable", "wire", "switchgear", "transformer", "breaker", "panel", "motor", "तार", "केबल", "ट्रांसफार्मर", "स्विचगियर", "पैनल", "बिजली", "सर्किट"],
    "crane": ["crane", "hoist", "hook", "sling", "trolley", "winch", "क्रेन", "हुक", "होइस्ट", "तार रस्सी"],
    "vehicle": ["truck", "dumper", "locomotive", "forklift", "wagon", "car", "ट्रक", "तरक", "डंपर", "गाड़ी", "लोकोमोटिव", "वैगन", "फोर्कलिफ्ट"],
}

_SYMPTOM_MAP = {
    "dizziness": ["dizzy", "dizziness", "lightheaded", "चक्कर", "सिर घूमना"],
    "headache": ["headache", "head pain", "सिर दर्द", "सर दर्द"],
    "breathing_difficulty": ["breathing", "breath", "suffocation", "shortness of breath", "choking", "सांस", "दम घुटना", "सांस फूलना"],
    "irritation": ["irritation", "eye irritation", "throat burning", "burning eyes", "जलन", "आंखों में जलन", "गले में जलन"],
    "burns": ["burn", "scald", "blister", "hot metal burn", "जल गया", "झुलस गया", "छाला"],
    "nausea_vomiting": ["nausea", "vomiting", "sick", "stomach", "उल्टी", "जी मिचलाना"],
    "unconscious": ["unconscious", "fainted", "collapsed", "passed out", "बेहोश", "अचेत", "गिर पड़ा"],
}

_WORD_NUMBERS = {
    "zero": 0, "none": 0, "nobody": 0, "no one": 0, "just me": 1, "only me": 1,
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "a few": 3, "couple": 2, "several": 5, "dozens": 20,
}

_NUMBER_PATTERN = re.compile(
    r"\b(\d+|zero|none|nobody|no one|just me|only me|one|two|three|four|five|six|seven|eight|nine|ten|a few|couple|several)\b",
    re.IGNORECASE,
)

# Semantic prototypes for intent alignment across English & Indian languages
_STANCE_PROFILES = {
    "affirmative": (
        "yes confirmed definitely active happening visible present true "
        "हाँ હા হ্যাঁ ஆம் అవును होय ಹೌದು അതെ ਹਾਂ ହଁ"
    ),
    "negative": (
        "no not none stopped cleared absent false negative "
        "नहीं ના না இல்லை కాదు नाही ಇಲ್ಲ ಇಲ್ಲ ਨਾ ନା"
    ),
    "uncertain": (
        "not sure don't know unknown maybe unclear not certain cannot see "
        "पता नहीं ખબર નથી নিশ্চিত নই தெரியாது తెలియదు माहित नाही ಗೊತ್ತಿಲ್ಲ അറിയില്ല ਪਤਾ ਨਹੀਂ ଜଣାନାହିଁ"
    ),
}

_WORD_NUMBERS = {
    "zero": 0, "none": 0, "nobody": 0, "no one": 0, "just me": 1, "only me": 1,
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "a few": 3, "couple": 2, "several": 5, "dozens": 20,
    # Indian languages numbers
    "एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पाँच": 5, "पांच": 5, "छह": 6, "सात": 7, "आठ": 8, "नौ": 9, "दस": 10,
    "দুই": 2, "তিন": 3, "চার": 4, "পাঁচ": 5,
    "ஒன்று": 1, "இரண்டு": 2, "மூன்று": 3, "நான்கு": 4, "ஐந்து": 5,
    "ఒకటి": 1, "రెండు": 2, "మూడు": 3, "నాలుగు": 4, "ఐదు": 5,
    "दोन": 2, "तीन": 3, "चार": 4, "पाच": 5, "સહા": 6,
    "એક": 1, "બે": 2, "ત્રણ": 3, "ચાર": 4, "પાંચ": 5,
    "ಒಂದು": 1, "ಎರಡು": 2, "ಮೂರು": 3, "ನಾಲ್ಕು": 4, "ಐದು": 5,
    "ഒന്ന്": 1, "രണ്ട്": 2, "മൂന്ന്": 3, "നാല്": 4, "അഞ്ച്": 5,
    "ਇੱਕ": 1, "ਦੋ": 2, "ਤਿੰਨ": 3, "ਚਾਰ": 4, "ਪੰਜ": 5,
    "ଏକ": 1, "ଦୁଇ": 2, "ତିନି": 3, "ଚାରି": 4, "ପାଞ୍ଚ": 5,
}

_NUMBER_PATTERN = re.compile(
    r"\b(\d+|zero|none|nobody|no one|just me|only me|one|two|three|four|five|six|seven|eight|nine|ten|a few|couple|several|"
    r"एक|दो|तीन|चार|पाँच|पांच|छह|सात|आठ|नौ|दस|দুই|তিন|চার|পাঁচ|ஒன்று|இரண்டு|மூன்று|நான்கு|ஐந்து|"
    r"ఒకటి|రెండు|మూడు|నాలుగు|ఐదు|दोन|पाच|સહા|એક|બે|ત્રણ|ચાર|પાંચ|ಒಂದು|ಎರಡು|ಮೂರು|ನಾಲ್ಕು|ಐದು|"
    r"ഒന്ന്|രണ്ട്|മൂന്ന്|നാല്|അഞ്ച്|ਇੱਕ|ਦੋ|ਤਿੰਨ|ਚਾਰ|ਪੰਜ|ଏକ|ଦୁଇ|ତିନି|ചାରି|ପାଞ୍ଚ)\b",
    re.IGNORECASE,
)

_stance_embeddings = None


def _get_stance_embeddings():
    global _stance_embeddings
    if _stance_embeddings is None:
        _stance_embeddings = {
            k: embeddings.encode([text])[0] for k, text in _STANCE_PROFILES.items()
        }
    return _stance_embeddings


def classify_answer_stance(answer_text: str) -> dict[str, float]:
    """Computes semantic similarity against affirmative, negative, and uncertain stances."""
    if not answer_text.strip():
        return {"affirmative": 0.0, "negative": 0.0, "uncertain": 1.0}

    vec = embeddings.encode([answer_text])[0]
    stances = _get_stance_embeddings()
    scores = {k: float(stances[k] @ vec) for k in stances}
    return scores


def identify_answer(question_text: str, answer_text: str) -> dict[str, Any]:
    """
    Extracts structured safety attributes from an individual question-answer turn.
    Supports English and 11 Indian languages.
    """
    lowered = answer_text.lower().strip()
    q_lowered = question_text.lower()
    stances = classify_answer_stance(answer_text)

    # 1. Observation mode (Saw vs Smelled vs Both vs Uncertain) across Indian languages
    observation_mode = "unspecified"
    saw_kws = ["saw", "see", "visible", "looked", "witnessed", "देखा", "দেখেছি", "பார்த்தேன்", "చూశాను", "पाहिला", "જોયો", "ನೋಡಿದೆ", "കണ്ടു", "ਦੇਖੀ", "ଦେଖିଲି"]
    smell_kws = ["smell", "smelled", "odor", "fumes", "गंध", "গন্ধ", "வாசனை", "వాసన", "वास", "ગંધ", "ವಾಸನೆ", "മണം", "ਗੰਧ", "ବାସ୍ନା"]
    has_saw = any(w in lowered for w in saw_kws)
    has_smell = any(w in lowered for w in smell_kws)
    if has_saw and has_smell:
        observation_mode = "both_seen_and_smelled"
    elif has_saw:
        observation_mode = "visual_confirmed"
    elif has_smell:
        observation_mode = "odor_only"
    elif stances["uncertain"] > stances["affirmative"] and stances["uncertain"] > 0.4:
        observation_mode = "uncertain"

    # 2. Hazard active status across Indian languages
    is_active = None
    active_kws = ["active", "still", "escaping", "leaking", "spreading", "ongoing", "हिसिंग", "जारी", "চলছে", "தொடர்கிறது", "కొనసాగుతోంది", "सुरू आहे", "ચાલુ છે", "ಮುಂದುವರಿಯುತ್ತಿದೆ", "തുടരുന്നു", "ਜਾਰੀ ਹੈ", "ଚାଲିଛି"]
    stopped_kws = ["stopped", "ceased", "not leaking", "shut off", "isolated", "रुक गया", "बंद", "நிறுத்தப்பட்டது", "ఆపివేశారు", "ಬಂದಾಗಿದೆ", "നിർത്തി", "ਬੰਦ"]
    if any(w in lowered for w in active_kws):
        is_active = True
    elif any(w in lowered for w in stopped_kws):
        is_active = False
    elif any(k in q_lowered for k in ["active", "leaking", "spread", "ongoing", "चालू", "जारी"]):
        if stances["affirmative"] > stances["negative"] and stances["affirmative"] > 0.35:
            is_active = True
        elif stances["negative"] > stances["affirmative"] and stances["negative"] > 0.35:
            is_active = False

    # 3. Equipment / Source identification
    identified_equipment = []
    for eq_type, kws in _EQUIPMENT_KEYWORDS.items():
        if any(kw in lowered for kw in kws):
            identified_equipment.append(eq_type)

    # 4. People count
    people_count = None
    num_match = _NUMBER_PATTERN.search(lowered)
    if num_match:
        token = num_match.group(1).lower()
        if token.isdigit():
            people_count = int(token)
        else:
            people_count = _WORD_NUMBERS.get(token)

    # 5. Symptoms detected
    symptoms_found = []
    for sym_name, sym_kws in _SYMPTOM_MAP.items():
        if any(skw in lowered for skw in sym_kws):
            symptoms_found.append(sym_name)

    # 6. Containment / Isolation status
    containment_status = "unknown"
    if any(w in lowered for w in ["cleared", "evacuated", "isolated", "cordoned", "notified control room", "खाली कराया"]):
        containment_status = "mitigated_or_evacuated"
    elif any(w in lowered for w in ["not reported", "not cleared", "no one knows", "still present", "नहीं किया"]):
        containment_status = "unmitigated"

    # 7. Confidence Score of this evidence
    clarity_score = 0.5
    if len(answer_text.split()) >= 3:
        clarity_score += 0.2
    if identified_equipment or symptoms_found or people_count is not None:
        clarity_score += 0.2
    if observation_mode in ["visual_confirmed", "both_seen_and_smelled"]:
        clarity_score += 0.1
    if stances["uncertain"] > 0.55:
        clarity_score -= 0.3
    evidence_score = round(max(0.1, min(1.0, clarity_score)), 2)

    return {
        "raw_answer": answer_text,
        "observation_mode": observation_mode,
        "is_active": is_active,
        "identified_equipment": identified_equipment,
        "people_count": people_count,
        "symptoms": symptoms_found,
        "containment_status": containment_status,
        "stance_scores": {k: round(v, 2) for k, v in stances.items()},
        "evidence_score": evidence_score,
    }


def aggregate_interview_findings(questions: list[str], answers: list[str]) -> dict[str, Any]:
    """
    Aggregates all question-answer turns in an interview into unified structured safety facts.
    """
    aggregated: dict[str, Any] = {
        "observation_mode": "unspecified",
        "is_hazard_active": None,
        "confirmed_equipment": [],
        "people_exposed_count": None,
        "reported_symptoms": [],
        "containment_status": "unmitigated",
        "total_evidence_score": 0.0,
        "turn_details": [],
    }

    if not answers:
        return aggregated

    scores = []
    all_equipment = set()
    all_symptoms = set()

    for q, a in zip(questions, answers):
        turn = identify_answer(q, a)
        aggregated["turn_details"].append(turn)
        scores.append(turn["evidence_score"])

        if turn["observation_mode"] != "unspecified" and aggregated["observation_mode"] == "unspecified":
            aggregated["observation_mode"] = turn["observation_mode"]

        if turn["is_active"] is not None:
            aggregated["is_hazard_active"] = turn["is_active"]

        for eq in turn["identified_equipment"]:
            all_equipment.add(eq)

        if turn["people_count"] is not None and aggregated["people_exposed_count"] is None:
            aggregated["people_exposed_count"] = turn["people_count"]

        for s in turn["symptoms"]:
            all_symptoms.add(s)

        if turn["containment_status"] != "unknown":
            aggregated["containment_status"] = turn["containment_status"]

    aggregated["confirmed_equipment"] = sorted(list(all_equipment))
    aggregated["reported_symptoms"] = sorted(list(all_symptoms))
    aggregated["total_evidence_score"] = round(sum(scores) / len(scores), 2) if scores else 0.5

    return aggregated
