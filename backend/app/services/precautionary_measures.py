"""
Dynamic Situation-Conditioned Precautionary Safety Measures Engine.
Grounded in Bokaro Steel Limited (BSL) Safety SOPs, dynamically tailored
to the exact incident facts and verification interview answers provided by the worker.
Supports 10 Indian languages (hi, bn, ta, te, mr, gu, kn, ml, pa, or) + English.
Urdu is strictly excluded.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from app.models import Ticket
from app.services import rag, translation, tts

logger = logging.getLogger(__name__)

PROMPT_QUESTION_LOCALIZED: dict[str, str] = {
    "en": "Would you like to hear the precautionary safety measures for your personal safety?",
    "hi": "क्या आप अपनी व्यक्तिगत सुरक्षा के लिए एहतियाती सुरक्षा उपाय सुनना चाहते हैं?",
    "bn": "আপনি কি আপনার ব্যক্তিগত সুরক্ষার জন্য সতর্কতামূলক ব্যবস্থা শুনতে চান?",
    "ta": "உங்கள் தனிப்பட்ட பாதுகாப்பிற்கான முன்னெச்சரிக்கை பாதுகாப்பு நடவடிக்கைகளை கேட்க விரும்புகிறீர்களா?",
    "te": "మీ వ్యక్తిగత భద్రత కోసం ముందస్తు రక్షణ చర్యలను వినాలనుకుంటున్నారా?",
    "mr": "तुम्हाला तुमच्या वैयक्तिक सुरक्षिततेसाठी खबरदारीचे उपाय ऐकायचे आहेत का?",
    "gu": "શું તમે તમારી વ્યક્તિગત સલામતી માટે સાવચેતીના પગલાં સાંભળવા માંગો છો?",
    "kn": "ನಿಮ್ಮ ವೈಯಕ್ತಿಕ ಸುರಕ್ಷತೆಗಾಗಿ ಮುನ್ನೆಚ್ಚರಿಕೆ ಕ್ರಮಗಳನ್ನು ಕೇಳಲು ನೀವು ಬಯಸುವಿರಾ?",
    "ml": "നിങ്ങളുടെ വ്യക്തിഗത സുരക്ഷയ്ക്കായുള്ള മുൻകരുതൽ നടപടികൾ കേൾക്കാൻ ആഗ്രഹിക്കുന്നുണ്ടോ?",
    "pa": "ਕੀ ਤੁਸੀਂ ਆਪਣੀ ਨਿੱਜੀ ਸੁਰੱਖਿਆ ਲਈ ਸਾਵਧਾਨੀ ਦੇ ਸੁਰੱਖਿਆ ਉਪਾਅ ਸੁਣਨਾ ਚਾਹੁੰਦੇ ਹੋ?",
    "or": "ଆପଣ କ'ଣ ନିଜ ବ୍ୟକ୍ତିଗତ ସୁରକ୍ଷା ପାଇଁ ସତର୍କତା ମୂଳକ ପଦକ୍ଷେପ ଶୁଣିବାକୁ ଚାହାଁନ୍ତି କି?",
}

CATEGORY_SOP_SOURCES: dict[str, dict[str, str]] = {
    "gas_leak": {
        "title": "Gas Leak Emergency Response Procedure",
        "code": "BSL/SOP/GAS-01",
        "file": "gas_leak_emergency_response.md",
    },
    "fire": {
        "title": "Fire Emergency Response Procedure",
        "code": "BSL/SOP/FIRE-02",
        "file": "fire_emergency_response.md",
    },
    "electrical_hazard": {
        "title": "Electrical Safety & Lockout-Tagout (LOTO) Procedure",
        "code": "BSL/SOP/ELEC-03",
        "file": "electrical_safety_lockout_tagout.md",
    },
    "electrical": {
        "title": "Electrical Safety & Lockout-Tagout (LOTO) Procedure",
        "code": "BSL/SOP/ELEC-03",
        "file": "electrical_safety_lockout_tagout.md",
    },
    "molten_metal_spill": {
        "title": "Molten Metal & Slag Spill Response Procedure",
        "code": "BSL/SOP/MET-04",
        "file": "molten_metal_spill_response.md",
    },
    "molten_metal": {
        "title": "Molten Metal & Slag Spill Response Procedure",
        "code": "BSL/SOP/MET-04",
        "file": "molten_metal_spill_response.md",
    },
    "chemical_spill": {
        "title": "Chemical Spill Response Procedure",
        "code": "BSL/SOP/CHEM-05",
        "file": "chemical_spill_response.md",
    },
    "confined_space_emergency": {
        "title": "Confined Space Emergency Response Procedure",
        "code": "BSL/SOP/CONF-06",
        "file": "confined_space_emergency_response.md",
    },
    "confined_space": {
        "title": "Confined Space Emergency Response Procedure",
        "code": "BSL/SOP/CONF-06",
        "file": "confined_space_emergency_response.md",
    },
    "crane_lifting_failure": {
        "title": "Crane & Heavy Rigging Safety Procedure",
        "code": "BSL/SOP/CRANE-07",
        "file": "crane_lifting_failure_response.md",
    },
    "crane_rigging": {
        "title": "Crane & Heavy Rigging Safety Procedure",
        "code": "BSL/SOP/CRANE-07",
        "file": "crane_lifting_failure_response.md",
    },
    "mechanical_failure": {
        "title": "Mechanical Isolation & Equipment Failure Procedure",
        "code": "BSL/SOP/MECH-08",
        "file": "mechanical_isolation_permit_to_work.md",
    },
    "conveyor": {
        "title": "Conveyor Safety & Emergency Stop Procedure",
        "code": "BSL/SOP/CONV-08",
        "file": "mechanical_isolation_permit_to_work.md",
    },
    "slip_fall": {
        "title": "Slip, Trip & Fall Prevention / Housekeeping Standard",
        "code": "BSL/SOP/SLIP-09",
        "file": "slip_fall_housekeeping.md",
    },
    "vehicle_traffic_incident": {
        "title": "Plant Vehicle & Heavy Traffic Safety Procedure",
        "code": "BSL/SOP/VEH-10",
        "file": "vehicle_traffic_incident_response.md",
    },
    "ppe_violation": {
        "title": "Mandatory Personal Protective Equipment Standard",
        "code": "BSL/SOP/PPE-11",
        "file": "ppe_requirements.md",
    },
}

DEFAULT_SOP_SOURCE = {
    "title": "Bokaro Steel General Industrial Safety Code",
    "code": "BSL/SOP/GEN-00",
    "file": "evacuation_assembly_point.md",
}

LOCALIZED_MEASURE_TITLES: dict[str, dict[str, str]] = {
    "evacuate": {
        "en": "Immediate Evacuation & Cordon Protocol",
        "hi": "तत्काल निकासी एवं सुरक्षा घेरा निर्देश",
        "bn": "অবিলম্বে প্রস্থান ও নিরাপত্তা বেষ্টনী নির্দেশ",
        "ta": "உடனடி வெளியேற்றம் மற்றும் பாதுகாப்பு எல்லை நெறிமுறை",
        "te": "తక్షణ తరలింపు మరియు భద్రతా హద్దుల ప్రొటోకాల్",
        "mr": "तातडीने स्थलांतर आणि सुरक्षा घेरा मार्गदर्शक",
        "gu": "તાત્કાલિક સ્થળાંતર અને સુરક્ષા કોર્ડન પ્રોટોકોલ",
        "kn": "ತಕ್ಷಣದ ಸ್ಥಳಾಂತರ ಮತ್ತು ಸುರಕ್ಷತಾ ಗಡಿ ಪ್ರೋಟೋಕಾಲ್",
        "ml": "ഉടനടിയുള്ള സുരക്ഷിത മാറ്റവും സുരക്ഷാ അതിർത്തിയും",
        "pa": "ਤੁਰੰਤ ਨਿਕਾਸੀ ਅਤੇ ਸੁਰੱਖਿਆ ਘੇਰਾ ਪ੍ਰੋਟੋਕੋਲ",
        "or": "ତୁରନ୍ତ ପ୍ରସ୍ଥାନ ଓ ସୁରକ୍ଷା ଘେରା ନିର୍ଦ୍ଦେଶ",
    },
    "life_safety_ppe": {
        "en": "Targeted Life-Safety & Protective Action",
        "hi": "लक्षित जीवन-सुरक्षा एवं सुरक्षात्मक कार्रवाई",
        "bn": "নির্দিষ্ট জীবন-সুরক্ষা ও সুরক্ষামূলক ব্যবস্থা",
        "ta": "இலக்கு வைக்கப்பட்ட உயிர் பாதுகாப்பு மற்றும் தடுப்பு நடவடிக்கை",
        "te": "లక్ష్యిత ప్రాణ రక్షణ మరియు రక్షణ చర్యలు",
        "mr": "लक्ष्यित जीवन-सुरक्षा आणि संरक्षणात्मक कृती",
        "gu": "લક્ષિત જીવન સુરક્ષા અને રક્ષણાત્મક પગલાં",
        "kn": "ನಿರ್ದಿಷ್ಟ ಜೀವ ಸುರಕ್ಷತೆ ಮತ್ತು ರಕ್ಷಣಾ ಕ್ರಮ",
        "ml": "ജീവൻരക്ഷാ സുരക്ഷയും മുൻകരുതൽ നടപടികളും",
        "pa": "ਜੀਵਨ-ਸੁਰੱਖਿਆ ਅਤੇ ਬਚਾਅ ਕਾਰਵਾਈ",
        "or": "ନିର୍ଦ୍ଦିଷ୍ଟ ଜୀବନ-ସୁରକ୍ଷା ଓ ପ୍ରତିଷେଧକ ପଦକ୍ଷେପ",
    },
    "donts": {
        "en": "Critical Situation Prohibitions (Don'ts)",
        "hi": "स्थिति-विशिष्ट गंभीर निषेध (क्या न करें)",
        "bn": "পরিস্থিতি-নির্দিষ্ট জরুরি নিষেধাজ্ঞা (যা করবেন না)",
        "ta": "முக்கிய சூழ்நிலை தடைகள் (செய்யக்கூடாதவை)",
        "te": "పరిస్థితికి సంబంధించిన ముఖ్యమైన నిషేధాలు (చేయకూడనివి)",
        "mr": "परिस्थितीनुसार गंभीर निर्बंध (काय करू नये)",
        "gu": "પરિસ્થિતિ-વિશિષ્ટ ગંભીર નિષેધ (શું ન કરવું)",
        "kn": "ನಿರ್ದಿಷ್ಟ ಪರಿಸ್ಥಿತಿಯ ಪ್ರಮುಖ ನಿಷೇಧಗಳು (ಮಾಡಬಾರದ ಕೆಲಸಗಳು)",
        "ml": "സാഹചര്യപരമായ കർശന വിലക്കുകൾ (ചെയ്യാൻ പാടില്ലാത്തവ)",
        "pa": "ਗੰਭੀਰ ਸੁਰੱਖਿਆ ਮਨਾਹੀਆਂ (ਕੀ ਨਹੀਂ ਕਰਨਾ)",
        "or": "ଜରୁରୀ ପରିସ୍ଥିତି ନିଷେଧ (କଣ କରିବେ ନାହିଁ)",
    },
    "emergency_contacts": {
        "en": "Incident Command & Emergency Dispatches",
        "hi": "आपदा नियंत्रण एवं तैनात आपातकालीन दस्ते",
        "bn": "জরুরি নির্দেশ ও মোতায়েন করা দল",
        "ta": "அவசர கட்டளை மற்றும் அனுப்பப்பட்ட குழுக்கள்",
        "te": "అత్యవసర ఆదేశాలు మరియు నియమించబడిన బృందాలు",
        "mr": "आपत्कालीन नियंत्रण आणि तैनात पथके",
        "gu": "કટોકટી આદેશ અને તૈનાત ટુકડીઓ",
        "kn": "ತುರ್ತು ಆದೇಶ ಮತ್ತು ನಿಯೋಜಿತ ತಂಡಗಳು",
        "ml": "അടിയന്തര നിയന്ത്രണവും നിയോഗിച്ച രക്ഷാസംഘങ്ങളും",
        "pa": "ਐਮਰਜੈਂਸੀ ਕਮਾਂਡ ਅਤੇ ਤਾਇਨਾਤ ਟੀਮਾਂ",
        "or": "ଜରୁରୀ ନିୟନ୍ତ୍ରଣ ଓ ମୁତୟନ ଜରୁରୀକାଳୀନ ଦଳ",
    },
}


def normalize_category(category: str) -> str:
    cat = (category or "").lower()
    if "gas" in cat:
        return "gas_leak"
    if "fire" in cat or "flame" in cat or "smoke" in cat:
        return "fire"
    if "elec" in cat or "shock" in cat or "voltage" in cat:
        return "electrical_hazard"
    if "molten" in cat or "metal" in cat or "slag" in cat:
        return "molten_metal_spill"
    if "chem" in cat or "acid" in cat or "toxic" in cat:
        return "chemical_spill"
    if "confined" in cat or "space" in cat or "tank interior" in cat or "manhole" in cat:
        return "confined_space_emergency"
    if "crane" in cat or "lift" in cat or "rigging" in cat or "hoist" in cat:
        return "crane_lifting_failure"
    if "conveyor" in cat or "belt" in cat:
        return "conveyor"
    if "mech" in cat or "machine" in cat or "pipe" in cat or "gear" in cat:
        return "mechanical_failure"
    if "slip" in cat or "fall" in cat or "trip" in cat:
        return "slip_fall"
    if "vehicle" in cat or "traffic" in cat or "truck" in cat or "dumper" in cat or "collision" in cat:
        return "vehicle_traffic_incident"
    if "ppe" in cat or "helmet" in cat or "glove" in cat:
        return "ppe_violation"
    return "default"


def extract_situation_facts(ticket: Ticket) -> dict[str, Any]:
    """
    Extracts high-resolution situational facts from the worker's initial description
    and the multi-turn verification interview answers.
    """
    answers_en = ticket.verification_answers_en or []
    answers_nat = ticket.verification_answers or []
    questions_nat = ticket.verification_questions or []
    desc_en = ticket.incident_description_en or ""
    desc_nat = ticket.incident_description or ""

    combined_en = f"{desc_en} " + " ".join(answers_en)
    combined_nat = f"{desc_nat} " + " ".join(answers_nat)
    text_en_low = combined_en.lower()

    # 1. Concrete Equipment Identification
    eq_name = "Plant Equipment / Facility"
    eq_name_hi = "संयंत्र उपकरण / स्थल"
    if any(w in text_en_low or w in combined_nat for w in ["crane", "क्रेन", "hoist", "catwalk", "gantry"]):
        eq_name = "Overhead EOT Crane & Gantry Runway"
        eq_name_hi = "ओवरहेड ईओटी क्रेन एवं गैन्ट्री रनवे"
    elif any(w in text_en_low or w in combined_nat for w in ["truck", "dumper", "ट्रक", "डंपर", "forklift", "locomotive"]):
        eq_name = "Heavy Transport Dumper & Plant Vehicle"
        eq_name_hi = "भारी परिवहन डंपर एवं संयंत्र वाहन"
    elif any(w in text_en_low or w in combined_nat for w in ["conveyor", "belt", "कन्वेयर", "बेल्ट", "roller"]):
        eq_name = "Raw Material Conveyor Belt System"
        eq_name_hi = "रॉ मटेरियल कन्वेयर बेल्ट सिस्टम"
    elif any(w in text_en_low or w in combined_nat for w in ["switchgear", "panel", "cable", "wire", "पैनल", "बिजली", "तार", "केबल", "breaker"]):
        eq_name = "High-Voltage Electrical Switchgear & Panel"
        eq_name_hi = "हाई-वोल्टेज इलेक्ट्रिकल स्विचगियर एवं पैनल"
    elif any(w in text_en_low or w in combined_nat for w in ["valve", "flange", "वाल्व", "flange leak", "gas line"]):
        eq_name = "Gas Distribution Pipeline & Isolation Valve"
        eq_name_hi = "गैस वितरण पाइपलाइन एवं आइसोलेशन वाल्व"
    elif any(w in text_en_low or w in combined_nat for w in ["ladle", "tundish", "furnace", "लैडल", "भट्ठी", "slag"]):
        eq_name = "Liquid Steel Ladle & Furnace Casthouse"
        eq_name_hi = "तरल धातु लैडल एवं ब्लास्ट फर्नेस कास्टहाउस"
    elif any(w in text_en_low or w in combined_nat for w in ["confined", "pit", "manhole", "गड्ढा", "मैनहोल", "tank interior"]):
        eq_name = "Confined Storage Vessel & Drainage Pit"
        eq_name_hi = "सीमित भंडारण वेसल एवं भूमिगत नाला/गड्ढा"
    elif any(w in text_en_low or w in combined_nat for w in ["acid", "chemical", "hcl", "एसिड", "तेजाब", "caustic", "pickling"]):
        eq_name = "Chemical Acid Storage & Pickling Line"
        eq_name_hi = "रासायनिक एसिड भंडारण एवं पिकलिंग लाइन"

    # 2. Number of personnel in danger / vicinity
    people_count = None
    num_match = re.search(
        r"\b(one|two|three|four|five|six|seven|eight|nine|ten|\d+)\s*(people|workers|persons|men|colleagues|लोग|कर्मचारी)?\b",
        text_en_low,
    )
    if num_match:
        token = num_match.group(1)
        w_map = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}
        people_count = int(token) if token.isdigit() else w_map.get(token)
    if not people_count:
        for hi_num, val in [("दस", 10), ("१०", 10), ("पांच", 5), ("५", 5), ("चार", 4), ("४", 4), ("तीन", 3), ("३", 3), ("दो", 2), ("२", 2), ("एक", 1), ("१", 1)]:
            if hi_num in combined_nat:
                people_count = val
                break

    # 3. Spread dynamics & severity
    is_spreading = any(
        w in text_en_low or w in combined_nat
        for w in ["fast", "rapid", "spreading", "heavy smoke", "dense", "out of control", "तेज", "तेजी", "फैल", "धुआं फैल", "धुआ बहल", "increasing", "getting worse"]
    )

    # 4. Shock victim / Trapped personnel
    has_shock_victim = any(
        w in text_en_low or w in combined_nat
        for w in ["stuck", "struck", "shock", "victim in contact", "direct contact", "electrocution", "power blow", "झटका लगा", "करंट लगा", "चिपक", "बिजली लगी", "आदमी गिरा"]
    )
    has_trapped_worker = any(
        w in text_en_low or w in combined_nat
        for w in ["trapped", "stuck inside", "cannot escape", "pinned", "फंसा", "दबा", "कैद", "अंदर फंसा"]
    )

    # 5. Breaker / LOTO status
    loto_tripped = any(
        w in text_en_low or w in combined_nat
        for w in ["tripped", "locked out", "loto", "power cut", "switched off", "power off", "breaker", "ब्रेकर ट्रिप", "बंद कर दिया", "मेन स्विच", "बिजली काट", "स्विच बंद"]
    )
    power_active = any(
        w in text_en_low or w in combined_nat
        for w in ["power on", "not tripped", "still live", "cannot cut", "बिजली चालू", "पावर नहीं कटा", "स्पार्किंग जारी"]
    )

    # 6. Manual suppression status
    uncontrolled = any(
        w in text_en_low or w in combined_nat
        for w in ["no", "cannot", "not available", "uncontrolled", "failed", "नहीं", "नहीं बुझा", "काबू नहीं", "बेकाबू", "आग ज्यादा", "too dangerous"]
    )

    # 7. Symptoms
    has_symptoms = any(
        w in text_en_low or w in combined_nat
        for w in ["dizzy", "dizziness", "choking", "breath", "unconscious", "fainted", "चक्कर", "दम घुटना", "बेहोश", "गिरा"]
    )

    # 8. Chemical / Water hazard interaction
    water_risk = any(
        w in text_en_low or w in combined_nat
        for w in ["water", "puddle", "drain", "rain", "पानी", "नाला", "गीला"]
    )

    # 9. Extract key worker verified observations for display
    verified_points_hi = []
    verified_points_en = []
    for i, ans in enumerate(answers_nat):
        if ans and len(ans.strip()) > 1:
            q_label = questions_nat[i] if i < len(questions_nat) else f"उत्तर {i+1}"
            verified_points_hi.append(f"{ans.strip()}")
    for i, ans in enumerate(answers_en):
        if ans and len(ans.strip()) > 1:
            verified_points_en.append(f"{ans.strip()}")

    return {
        "equipment_en": eq_name,
        "equipment_hi": eq_name_hi,
        "people_count": people_count,
        "is_spreading": is_spreading,
        "has_shock_victim": has_shock_victim,
        "has_trapped_worker": has_trapped_worker,
        "loto_tripped": loto_tripped,
        "power_active": power_active,
        "uncontrolled": uncontrolled,
        "has_symptoms": has_symptoms,
        "water_risk": water_risk,
        "zone": ticket.zone_id or "Incident Area",
        "verified_answers_hi": verified_points_hi,
        "verified_answers_en": verified_points_en,
        "raw_description_hi": desc_nat,
        "raw_description_en": desc_en,
    }


def build_situation_measures(
    category: str,
    sit: dict[str, Any],
    lang: str = "en",
) -> tuple[list[dict[str, Any]], str, str]:
    """
    Constructs 4 distinct, situation-conditioned, authoritative precautionary measures
    grounded directly in the worker's reported situation and Bokaro SOPs.
    Returns: (measures_list, spoken_summary_en, spoken_summary_hi)
    """
    cat_key = normalize_category(category)
    eq_en = sit["equipment_en"]
    eq_hi = sit["equipment_hi"]
    zone = sit["zone"]
    people = sit["people_count"]
    spreading = sit["is_spreading"]
    shock_victim = sit["has_shock_victim"]
    trapped = sit["has_trapped_worker"]
    loto = sit["loto_tripped"]
    power_active = sit["power_active"]
    symptoms = sit["has_symptoms"]
    water_risk = sit["water_risk"]

    # Formulate verified context preface
    v_hi = " | ".join(sit["verified_answers_hi"][:2]) if sit["verified_answers_hi"] else sit["raw_description_hi"][:60]
    v_en = " | ".join(sit["verified_answers_en"][:2]) if sit["verified_answers_en"] else sit["raw_description_en"][:60]
    pref_hi = f"⚠️ आपके इनपुट ('{v_hi}'): " if v_hi else ""
    pref_en = f"⚠️ Based on verified report ('{v_en}'): " if v_en else ""

    # =========================================================================
    # 1. GAS LEAK
    # =========================================================================
    if cat_key == "gas_leak":
        evac_en = (
            f"{pref_en}UPWIND & CROSSWIND 100M CLEARANCE: Toxic/flammable gas release from {eq_en} in Zone {zone}. "
            f"Observe plant windsock immediately; evacuate perpendicular (90 degrees crosswind) and assemble upwind. "
            f"STRICTLY avoid cable basements, pipe trenches, or ground pits where dense CO/BFG gas accumulates."
        )
        evac_hi = (
            f"{pref_hi}हवा के विपरीत (अपविंड) 100 मीटर सुरक्षित दूरी: ज़ोन {zone} में {eq_hi} से गैस रिसाव हुआ है। "
            f"प्लांट विंडसॉक देखकर हवा की दिशा के 90 डिग्री कोण पर बाहर निकलें और हवा के विपरीत ऊंचे स्थान पर जाएं। "
            f"केबल बेसमेंट, भूमिगत गड्ढों या नालों में बिल्कुल न जाएं जहां भारी गैस जमा होती है।"
        )
        chk_en = f"Evacuated 100m upwind from {eq_en} away from low-lying trenches"
        chk_hi = f"{eq_hi} से हवा के विपरीत 100 मीटर दूर ऊंचे स्थान पर पहुंचे"

        if symptoms:
            life_en = (
                f"{pref_en}EMERGENCY OXYGEN RESCUE: Symptoms reported among personnel. "
                f"Anyone with headache, nausea, or dizziness must be administered 100% medical oxygen immediately. "
                f"Responders MUST NOT enter without positive-pressure Self-Contained Breathing Apparatus (SCBA)."
            )
            life_hi = (
                f"{pref_hi}आपातकालीन ऑक्सीजन व SCBA रेस्क्यू: कर्मियों में चक्कर/बेहोशी के लक्षण दर्ज हैं। "
                f"प्रभावित कर्मियों को तुरंत 100% मेडिकल ऑक्सीजन दें। "
                f"बिना पॉजिटिव-प्रेशर SCBA (सेल्फ-कंटेन्ड ब्रीदिंग अपेरटस) के कोई भी बचावकर्मी गैस क्षेत्र में प्रवेश न करे।"
            )
            chk_life_en = "Administered emergency medical oxygen and verified SCBA deployment"
            chk_life_hi = "प्रभावित कर्मियों को ऑक्सीजन दी और SCBA गियर पहना"
        else:
            life_en = (
                f"MANDATORY SCBA & ESCAPE HOODS: Continuous gas monitoring required. "
                f"Don 15-minute emergency escape hoods before operating manual valves. Standard particulate masks offer zero defense against CO."
            )
            life_hi = (
                f"अनिवार्य SCBA व एस्केप हुड: गैस क्षेत्र में साधारण डस्ट मास्क CO गैस से कोई सुरक्षा नहीं देता। "
                f"वाल्व के पास जाने से पहले 15 मिनट वाला आपातकालीन रेस्पिरेटरी एस्केप हुड या SCBA अवश्य पहनें।"
            )
            chk_life_en = "Donned positive-pressure SCBA escape hoods"
            chk_life_hi = "आपातकालीन एस्केप हुड / SCBA मास्क पहना"

        dont_en = (
            "ZERO IGNITION ENFORCEMENT: Absolutely NO mobile phone usage, radio transmission, lighter sparks, or vehicle ignition within 100m. "
            "Do not operate electrical light switches or ventilation blowers that could generate static spark."
        )
        dont_hi = (
            "स्पार्क व मोबाइल फोन पूर्ण प्रतिबंध: 100 मीटर के दायरे में मोबाइल फोन, टॉर्च स्विच, वाहन स्टार्ट करना या सिगरेट लाइटर सख्त मना है। "
            "बिजली का कोई भी स्विच चालू/बंद न करें जिससे स्पार्क पैदा हो सके।"
        )
        chk_dont_en = "Prohibited all phone use, vehicles, and ignition sources in gas envelope"
        chk_dont_hi = "गैस क्षेत्र में मोबाइल फोन व बिजली स्विच पर पूर्ण रोक लगाई"

        cmd_en = (
            "BOKARO GAS SAFETY SQUAD: Bokaro Gas Safety Station (Ext 2222) and Central Emergency Control (Ext 101) notified. "
            "Plant Ambulance (Ext 102) positioned at upwind perimeter checkpoint."
        )
        cmd_hi = (
            "बोकारो गैस सुरक्षा दस्ता: गैस सेफ्टी स्टेशन (2222) और सेंट्रल इमरजेंसी कंट्रोल (101) को तत्काल सूचित किया गया। "
            "प्लांट मेडिकल एम्बुलेंस (102) को हवा के विपरीत चेकपॉइंट पर तैनात किया गया।"
        )
        chk_cmd_en = "Coordinated with Bokaro Gas Safety Squad (2222) and Ambulance (102)"
        chk_cmd_hi = "गैस सेफ्टी स्टेशन (2222) और एम्बुलेंस (102) से समन्वय स्थापित किया"

    # =========================================================================
    # 2. FIRE
    # =========================================================================
    elif cat_key == "fire":
        drop_zone = "30-meter drop zone below gantry" if "crane" in eq_en.lower() else "30-meter perimeter"
        drop_zone_hi = "क्रेन गैन्ट्री के नीचे 30 मीटर का दायरा" if "crane" in eq_en.lower() else "30 मीटर का सुरक्षा घेरा"
        evac_en = (
            f"{pref_en}EXCLUSION ZONE CORDON: Fire active on {eq_en} in Zone {zone}. "
            f"Clear at least a {drop_zone} immediately. Keep crane runway stairs and fire engine access lanes completely free."
        )
        evac_hi = (
            f"{pref_hi}तत्काल सुरक्षा घेरा: ज़ोन {zone} में {eq_hi} में आग की स्थिति है। "
            f"{drop_zone_hi} तुरंत खाली कराएं। फायर ब्रिगेड के वाहनों के आने का रास्ता पूरी तरह साफ रखें।"
        )
        chk_en = f"Cleared and cordoned 30m perimeter around {eq_en}"
        chk_hi = f"{eq_hi} के चारों ओर 30 मीटर का घेरा बनाया और रास्ता साफ रखा"

        if spreading:
            life_en = (
                f"{pref_en}SMOKE & THERMAL EVACUATION: Dense toxic smoke is spreading rapidly. "
                f"Stay crouched beneath the rising thermal ceiling. Don wet cloth or smoke hood over mouth and nose; never run upright through smoke corridors."
            )
            life_hi = (
                f"{pref_hi}घने धुएं से बचाव: आग और विषाक्त धुआं तेजी से फैल रहा है। "
                f"धुएं की चादर से नीचे झुककर चलें। नाक-मुंह पर गीला कपड़ा या स्मोक मास्क रखें; धुएं के बीच सीधे खड़े होकर न दौड़ें।"
            )
            chk_life_en = "Evacuated below thermal smoke layer using respiratory cover"
            chk_life_hi = "धुएं से नीचे झुककर सुरक्षित बाहर निकले"
        else:
            life_en = (
                "PROTECTIVE FIREFIGHTING GEAR: Personnel operating in perimeter must wear fire-retardant suits, safety goggles, and heavy leather gauntlets. "
                "Check headcounts against muster sheet immediately."
            )
            life_hi = (
                "अग्नि-रोधी सुरक्षा उपकरण: अग्निशमन क्षेत्र के आसपास कर्मी फायर-रिटार्डेंट सूट, सुरक्षा चश्मा और लेदर दस्ताने पहनें। "
                "असेंबली पॉइंट पर सभी कर्मियों की हाजिरी लें।"
            )
            chk_life_en = "Verified fire PPE compliance and muster point roll-call"
            chk_life_hi = "फायर सुरक्षा गियर पहना और कर्मियों की हाजिरी सुनिश्चित की"

        dont_en = (
            f"WATER RESTRICTION ON {eq_en.upper()}: Never apply straight water streams on electrical cables, oil sumps, or machinery. "
            f"Use ONLY CO2 or Dry Chemical Powder (DCP) extinguishers. Do not re-enter burning bays to retrieve personal tools."
        )
        dont_hi = (
            f"{eq_hi} पर पानी का उपयोग पूर्णतः वर्जित: बिजली के तारों, तेल की टंकियों या मशीनरी पर पानी का पाइप न मारें। "
            f"केवल CO2 या ड्राई केमिकल पाउडर (DCP) बुझाने वाले यंत्रों का प्रयोग करें। सामान निकालने के लिए आग में वापस न जाएं।"
        )
        chk_dont_en = f"Enforced strict water ban and DCP extinguisher use on {eq_en}"
        chk_dont_hi = f"{eq_hi} पर पानी के उपयोग पर रोक और केवल DCP/CO2 का उपयोग सुनिश्चित किया"

        cmd_en = (
            f"BSL FIRE BRIGADE DISPATCH: Bokaro Fire Crash Tenders (Ext 101 / 3333) en route to {eq_en} in Zone {zone}. "
            "Plant Trauma Unit (Ext 102) stationed at Zone muster point."
        )
        cmd_hi = (
            f"बीएसएल फायर ब्रिगेड रवाना: प्लांट फायर टेंडर (101 / 3333) ज़ोन {zone} में {eq_hi} के लिए रवाना हो चुके हैं। "
            "मेडिकल ट्रॉमा एम्बुलेंस (102) असेंबली पॉइंट पर तैनात है।"
        )
        chk_cmd_en = "Confirmed BSL Fire Brigade (101) & Medical Ambulance (102) en route"
        chk_cmd_hi = "फायर ब्रिगेड (101) और एम्बुलेंस (102) के मौके पर पहुंचने की पुष्टि की"

    # =========================================================================
    # 3. ELECTRICAL HAZARD
    # =========================================================================
    elif cat_key == "electrical_hazard":
        evac_en = (
            f"{pref_en}10-METER STEP-POTENTIAL BOUNDARY: Live electrical fault on {eq_en} in Zone {zone}. "
            f"Establish a strict 10-meter (33-foot) perimeter. Never take large steps across wet floors—shuffle feet together to avoid fatal step-voltage differences."
        )
        evac_hi = (
            f"{pref_hi}10 मीटर स्टेप-पोटेंशियल सुरक्षा घेरा: ज़ोन {zone} में {eq_hi} पर बिजली का फॉल्ट हुआ है। "
            f"कम से कम 10 मीटर का दायरा खाली रखें। गीले फर्श पर बड़े कदम न रखें—पैरों को सटाकर घसीटते हुए चलें ताकि जानलेवा अर्थ-करंट का झटका न लगे।"
        )
        chk_en = f"Cordoned 10m step-potential boundary around {eq_en}"
        chk_hi = f"{eq_hi} के चारों ओर 10 मीटर का विद्युत सुरक्षा घेरा बनाया"

        if shock_victim:
            life_en = (
                f"{pref_en}ZERO-TOUCH RESCUE PROTOCOL: Person reported in contact with electricity. "
                f"DO NOT touch victim with bare hands or ordinary clothes. Use certified fiberglass non-conductive rescue hook or dry timber pole to disengage. "
                f"Verify zero voltage before skin contact; administer CPR immediately if pulseless."
            )
            life_hi = (
                f"{pref_hi}जीरो-टच रेस्क्यू निर्देश: व्यक्ति बिजली के संपर्क में बताया गया है। "
                f"पीड़ित को नंगे हाथों या कपड़ों से सीधे न छुएं! केवल प्रमाणित फाइबरग्लास इंसुलेटेड रेस्क्यू हुक या सूखी लकड़ी के डंडे से अलग करें। "
                f"छूने से पहले पावर कट की पुष्टि करें और सांस न चलने पर तुरंत सीपीआर (CPR) दें।"
            )
            chk_life_en = "Rescued shock victim with non-conductive fiberglass hook and began CPR"
            chk_life_hi = "पीड़ित को इंसुलेटेड हुक से अलग किया और प्राथमिक उपचार शुरू किया"
        else:
            life_en = (
                "DIELECTRIC PPE MANDATE: Responders must wear Class-E electrical rated safety helmet, dielectric 11kV gloves, and insulated rubber boots. "
                "Verify Lockout/Tagout (LOTO) padlocks on feeder breaker before approaching."
            )
            life_hi = (
                "विद्युत-रोधी (Dielectric) PPE: मौके पर मौजूद कर्मी 11kV इंसुलेटेड रबर दस्ताने, क्लास-E सुरक्षा हेलमेट और डाइइलेक्ट्रिक जूते पहनें। "
                "पैनल के पास जाने से पहले फीडर ब्रेकर पर LOTO ताला लगाने की पुष्टि करें।"
            )
            chk_life_en = "Inspected 11kV dielectric gloves and insulated boots"
            chk_life_hi = "11kV रबर दस्ताने और इंसुलेटेड जूतों की जांच की"

        dont_en = (
            f"LOCKOUT INTEGRITY & WATER PROHIBITION: Never reset tripped switchgear breakers without written clearance from Electrical Incharge. "
            f"Absolutely FORBIDDEN to use water hoses or damp cloths near {eq_en}."
        )
        dont_hi = (
            f"{eq_hi} पर पानी व जबरन रीसेट वर्जित: बिना इलेक्ट्रिकल इंचार्ज की लिखित अनुमति के ट्रिप ब्रेकर को दोबारा चालू न करें। "
            f"पैनल या केबल के पास पानी, गीला कपड़ा या पानी की नली ले जाना पूरी तरह प्रतिबंधित है।"
        )
        chk_dont_en = f"Prohibited breaker reset and all water application near {eq_en}"
        chk_dont_hi = f"{eq_hi} पर बिना अनुमति स्विच चालू करने और पानी डालने पर रोक लगाई"

        cmd_en = (
            "ELECTRICAL SUBSTATION COMMAND: Substation Control Room (Ext 3111) notified for feeder isolation. "
            "Emergency Medical Trauma Ambulance (Ext 102) dispatched with AED Defibrillator."
        )
        cmd_hi = (
            "इलेक्ट्रिकल सबस्टेशन कमांड: सबस्टेशन कंट्रोल रूम (3111) को पावर कट के लिए सूचित किया गया। "
            "मेडिकल ट्रॉमा एम्बुलेंस (102) ऑटोमेटेड डिफिब्रिलेटर (AED) सहित मौके पर भेजी गई।"
        )
        chk_cmd_en = "Coordinated with Substation (3111) and Trauma Ambulance (102)"
        chk_cmd_hi = "सबस्टेशन कंट्रोल (3111) और एम्बुलेंस (102) से संपर्क किया"

    # =========================================================================
    # 4. CHEMICAL SPILL
    # =========================================================================
    elif cat_key == "chemical_spill":
        evac_en = (
            f"{pref_en}CORROSIVE RUNOFF CONTAINMENT: Chemical release from {eq_en} in Zone {zone}. "
            f"Establish a 25-meter exclusion boundary. Immediately place dry sand or sodium bicarbonate booms across drains to block chemical entering cooling waterways."
        )
        evac_hi = (
            f"{pref_hi}रासायनिक बहाव व नाला रोकथाम: ज़ोन {zone} में {eq_hi} से केमिकल/एसिड का रिसाव हुआ है। "
            f"25 मीटर का घेरा बनाएं। नाले और ड्रेन में सूखी रेत या सोडियम बाइकार्बोनेट की बोरियां लगाकर रसायन को पानी में बहने से तुरंत रोकें।"
        )
        chk_en = f"Blocked storm drains and cordoned 25m spill perimeter around {eq_en}"
        chk_hi = f"नालों में केमिकल जाने से रोका और 25 मीटर का घेरा बनाया"

        life_en = (
            f"{pref_en}CHEMICAL PPE & EYEWASH PROTOCOL: Don heavy chemical-resistant butyl rubber suits, neoprene gloves, and full-face splash shields. "
            f"If skin contact occurs, drench under emergency safety shower for at least 15 minutes continuously; do not rub skin."
        )
        life_hi = (
            f"{pref_hi}केमिकल सूट व आईवॉश निर्देश: ब्यूटाइल रबर केमिकल सूट, नियोप्रिन दस्ताने और फुल-फेस शील्ड पहनें। "
            f"त्वचा पर केमिकल गिरने पर कम से कम 15 मिनट तक लगातार सेफ्टी शॉवर / आईवॉश स्टेशन पर पानी से धोएं; त्वचा को रगड़ें नहीं।"
        )
        chk_life_en = "Donned butyl chemical PPE and readied 15-minute emergency shower"
        chk_life_hi = "केमिकल सुरक्षा सूट पहना और इमरजेंसी आईवॉश शॉवर तैयार रखा"

        dont_en = (
            "ZERO NEUTRALIZATION GUESSWORK: Do NOT spray strong acid with concentrated water jet which produces violent heat and acid mist. "
            "Never step into liquid puddles or enter chemical vapors without organic vapor/acid cartridge respirator."
        )
        dont_hi = (
            "सीधे पानी की धार न मारें: एसिड या तेजाब पर तेज पानी की धार न मारें जिससे तेजाब उछल सकता है और भाप बन सकती है। "
            "बिना केमिकल रेस्पिरेटर के वाष्प वाले क्षेत्र में प्रवेश न करें और केमिकल के गड्ढों में पैर न रखें।"
        )
        chk_dont_en = "Prohibited high-pressure water spray onto chemical spill"
        chk_dont_hi = "केमिकल पर सीधे तेज पानी मारने और बिना मास्क जाने पर रोक लगाई"

        cmd_en = (
            "BSL HAZMAT DISPATCH: Chemical Safety Cell (Ext 4444) and Fire Station (Ext 101) notified. "
            "Plant Trauma Unit (Ext 102) dispatched with chemical burn decontamination kit."
        )
        cmd_hi = (
            "बीएसएल हैज़मैट दस्ता: केमिकल सेफ्टी सेल (4444) और फायर स्टेशन (101) को सूचित किया गया। "
            "मेडिकल ट्रॉमा टीम (102) केमिकल बर्न उपचार किट के साथ मौके पर पहुंच रही है।"
        )
        chk_cmd_en = "Notified Hazmat Cell (4444) and Burn Treatment Unit (102)"
        chk_cmd_hi = "हैज़मैट सेल (4444) और बर्न मेडिकल टीम (102) को सूचित किया"

    # =========================================================================
    # 5. MOLTEN METAL & SLAG SPILL
    # =========================================================================
    elif cat_key == "molten_metal_spill":
        evac_en = (
            f"{pref_en}30-METER THERMAL RADIUS: Molten steel/slag breakout from {eq_en} in Zone {zone}. "
            f"Cordon at least 30 meters radially. Move perpendicular to molten stream toward elevated, dry concrete floors."
        )
        evac_hi = (
            f"{pref_hi}30 मीटर थर्मल सुरक्षा घेरा: ज़ोन {zone} में {eq_hi} से पिघली धातु/स्लैग का रिसाव हुआ है। "
            f"कम से कम 30 मीटर का दायरा खाली कराएं। धातु के बहाव से लंबवत होकर ऊंचे, सूखे कंक्रीट फर्श की ओर हटें।"
        )
        chk_en = f"Cleared 30m radius around molten breakout from {eq_en}"
        chk_hi = f"{eq_hi} से पिघली धातु के चारों ओर 30 मीटर का दायरा सुरक्षित किया"

        life_en = (
            "ALUMINIZED SUIT & ZERO-MOISTURE CHECK: Don full aluminized heat-reflective coat, blue cobalt face shield, and spats. "
            "CRITICAL: Inspect flooring in path of metal—verify NO water puddles, damp debris, or wet scale exist to prevent steam explosions."
        )
        life_hi = (
            "एल्युमिनाइज्ड सूट व नमी-रहित फर्श जांच: गर्मी-रोधी एल्युमिनाइज्ड कोट, कोबाल्ट-ब्लू फेस शील्ड और लेग गार्ड पहनें। "
            "अति महत्वपूर्ण: पिघली धातु के रास्ते में फर्श पर पानी या नमी बिल्कुल नहीं होनी चाहिए, अन्यथा भयानक भाप विस्फोट होगा।"
        )
        chk_life_en = "Inspected aluminized foundry PPE and cleared floor moisture"
        chk_life_hi = "एल्युमिनाइज्ड सूट पहना और फर्श पर पानी न होने की पुष्टि की"

        dont_en = (
            "ABSOLUTE ZERO-WATER BAN: Absolutely FORBIDDEN to spray water hoses or throw damp earth onto liquid steel or slag. "
            "Do not allow overhead cranes to travel directly over molten pool until thermal dissipation is confirmed."
        )
        dont_hi = (
            "पानी का उपयोग पूर्णतः वर्जित: पिघली धातु या स्लैग पर पानी की नली या गीली वस्तुएं फेंकना सख्त मना है। "
            "जब तक धातु ठंडी न हो जाए, क्रेन को छलकन वाले क्षेत्र के ऊपर से न ले जाएं।"
        )
        chk_dont_en = "Enforced absolute zero-water mandate on molten metal breakout"
        chk_dont_hi = "पिघली धातु पर पानी न डालने के सख्त नियम का पालन कराया"

        cmd_en = (
            "FURNACE & CASTHOUSE COMMAND: Blast Furnace Shift Superintendent (Ext 2400) and Central Fire (Ext 101) notified. "
            "Burn Trauma Ambulance (Ext 102) stationed at casthouse gate."
        )
        cmd_hi = (
            "ब्लास्ट फर्नेस कमांड: फर्नेस शिफ्ट अधीक्षक (2400) और फायर स्टेशन (101) को सूचित किया गया। "
            "बर्न ट्रॉमा एम्बुलेंस (102) कास्टहाउस गेट पर तैनात की गई।"
        )
        chk_cmd_en = "Coordinated with Casthouse Command (2400) and Ambulance (102)"
        chk_cmd_hi = "कास्टहाउस कमांड (2400) और बर्न एम्बुलेंस (102) से समन्वय किया"

    # =========================================================================
    # 6. CRANE & HEAVY LIFTING FAILURE
    # =========================================================================
    elif cat_key == "crane_lifting_failure":
        evac_en = (
            f"{pref_en}GANTRY DROP-ZONE CORDON: Hoist/rigging structural failure on {eq_en} in Zone {zone}. "
            f"Establish a ground perimeter equal to 1.5 times the boom/hook elevation (minimum 25m). No worker may stand or walk below the suspended load."
        )
        evac_hi = (
            f"{pref_hi}क्रेन ड्रॉप-ज़ोन सुरक्षा घेरा: ज़ोन {zone} में {eq_hi} में लिफ्टिंग/रोप की खराबी है। "
            f"लटकते हुए लोड के नीचे कम से कम 25 मीटर का दायरा लाल रिबन से घेरें। किसी भी व्यक्ति को लोड या गैन्ट्री के नीचे खड़ा न होने दें।"
        )
        chk_en = f"Enforced 25m drop-zone exclusion under {eq_en}"
        chk_hi = f"{eq_hi} के नीचे 25 मीटर का डेंजर ज़ोन खाली कराया"

        life_en = (
            f"{pref_en}CATWALK & RIGGER SAFETY: Personnel securing the perimeter must wear heavy-duty industrial helmets with chin-strap and steel-toe boots. "
            f"If crane operator is stranded in elevated cab, do NOT permit jumping—deploy aerial rescue basket with harness tie-off."
        )
        life_hi = (
            f"{pref_hi}क्रेन केबिन व रिगर सुरक्षा: सुरक्षा घेरे पर तैनात कर्मी चिन-स्ट्रैप सहित हेलमेट और स्टील-टो जूते पहनें। "
            f"यदि ऑपरेटर क्रेन केबिन में फंसा है, तो उसे कूदने न दें—सेफ्टी हार्नेस और एरियल बास्केट के साथ रेस्क्यू टीम का इंतजार करें।"
        )
        chk_life_en = "Secured rigger PPE and prepared aerial cabin rescue line"
        chk_life_hi = "सुरक्षा गियर पहना और क्रेन ऑपरेटर के सुरक्षित रेस्क्यू की तैयारी की"

        dont_en = (
            "ZERO SUSPENDED LOAD TRAVERSAL: Strictly prohibited from attempting to pull dangling wire ropes or taglines by hand while load is unbalanced. "
            "Do not operate cross-travel or hoist motors until structural rigging is inspected."
        )
        dont_hi = (
            "लटकते लोड को हाथ से न छुएं: लटकते हुए लोड या टूटे वायर रोप को हाथों से खींचने की कोशिश न करें। "
            "मैकेनिकल जांच से पहले क्रेन के मोटर या ट्रॉली को चलाने का प्रयास सख्त मना है।"
        )
        chk_dont_en = "Prohibited manual line pulling and unapproved crane travel"
        chk_dont_hi = "लटकते लोड को हाथ से खींचने या क्रेन चलाने पर रोक लगाई"

        cmd_en = (
            "CRANE MAINTENANCE & RESCUE SQUAD: Heavy Rigging & Crane Department (Ext 2700) and Central Safety (Ext 3333) dispatched. "
            "Emergency Crane Hydraulic Rescue Tender on standby."
        )
        cmd_hi = (
            "क्रेन मेंटेनेंस व रेस्क्यू दस्ता: हेवी रिगिंग व क्रेन विभाग (2700) और प्लांट सेफ्टी (3333) को भेजा गया। "
            "हाइड्रोलिक रेस्क्यू क्रेन स्टैंडबाय पर रखी गई।"
        )
        chk_cmd_en = "Notified Crane Maintenance (2700) and Rigging Squad"
        chk_cmd_hi = "क्रेन मेंटेनेंस (2700) और रिगिंग टीम को तैनात किया"

    # =========================================================================
    # 7. CONFINED SPACE EMERGENCY
    # =========================================================================
    elif cat_key == "confined_space_emergency":
        evac_en = (
            f"{pref_en}ENTRY HATCH LOCKDOWN: Atmospheric hazard inside {eq_en} in Zone {zone}. "
            f"Seal the manhole entrance immediately to prevent unequipped workers from rushing in. Maintain 10m perimeter around hatch."
        )
        evac_hi = (
            f"{pref_hi}मैनहोल प्रवेश तत्काल बंद: ज़ोन {zone} में {eq_hi} के अंदर जहरीली गैस/ऑक्सीजन की कमी की आपात स्थिति है। "
            f"मैनहोल के प्रवेश द्वार को तुरंत रोकें ताकि कोई बिना तैयारी अंदर न घुसे। हैच के बाहर 10 मीटर का घेरा बनाएं।"
        )
        chk_en = f"Sealed manhole hatch and cordoned 10m perimeter around {eq_en}"
        chk_hi = f"{eq_hi} के मैनहोल गेट को बंद किया और 10 मीटर का घेरा बनाया"

        life_en = (
            f"{pref_en}FORCED VENTILATION & TRIPOD WINCH: Run explosion-proof air blowers continuously into vessel. "
            f"Rescuers MUST wear airline breathing apparatus or 30-minute SCBA with full-body harness connected to retrieval tripod winch. Never enter without standby attendant."
        )
        life_hi = (
            f"{pref_hi}जबरन वेंटिलेशन व ट्राइपॉड विंच: टैंक में तुरंत एक्सप्लोजन-प्रूफ ब्लोअर से ताजी हवा भेजें। "
            f"बचावकर्मियों के लिए 30 मिनट का SCBA और सेफ्टी हार्नेस पहनकर ट्राइपॉड विंच से बंधना अनिवार्य है। बाहर एक अटेंडेंट खड़ा होना जरूरी है।"
        )
        chk_life_en = "Initiated forced air purge and readied tripod retrieval winch"
        chk_life_hi = "हवा का वेंटिलेशन शुरू किया और ट्राइपॉड रेस्क्यू विंच तैयार की"

        dont_en = (
            "ZERO UNASSISTED ENTRY: Over 60% of confined space fatalities are secondary rescuers rushing in without SCBA. "
            "Under NO circumstances step through the manway without verified multi-gas testing (O2 > 19.5%, CO < 25ppm)."
        )
        dont_hi = (
            "बिना उपकरण अंदर घुसना सख्त मना: 60% से अधिक मौतें बिना मास्क अंदर बचाने दौड़े साथियों की होती हैं। "
            "जब तक 4-गैस डिटेक्टर से ऑक्सीजन 19.5% से अधिक और CO सुरक्षित न पाई जाए, अंदर कदम न रखें।"
        )
        chk_dont_en = "Prohibited unassisted entry without SCBA and gas clearance"
        chk_dont_hi = "बिना गैस टेस्टिंग और SCBA के अंदर जाने पर पूर्ण रोक लगाई"

        cmd_en = (
            "CONFINED SPACE RESCUE TEAM: Bokaro Specialized Rescue Team (Ext 2222) and Trauma Ambulance (Ext 102) dispatched. "
            "Atmospheric testing specialist en route."
        )
        cmd_hi = (
            "कन्फाइंड स्पेस स्पेशल रेस्क्यू टीम: बोकारो स्पेशल रेस्क्यू टीम (2222) और मेडिकल ट्रॉमा एम्बुलेंस (102) रवाना। "
            "गैस टेस्टिंग विशेषज्ञ मौके पर पहुंच रहे हैं।"
        )
        chk_cmd_en = "Confirmed Confined Space Rescue Team (2222) and Ambulance (102)"
        chk_cmd_hi = "स्पेशल रेस्क्यू टीम (2222) और एम्बुलेंस (102) को तैनात किया"

    # =========================================================================
    # 8. CONVEYOR & MECHANICAL FAILURE
    # =========================================================================
    elif cat_key in ["conveyor", "mechanical_failure"]:
        evac_en = (
            f"{pref_en}PULL-CORD STOP & MECHANICAL CLEARANCE: Jammed/failing drive on {eq_en} in Zone {zone}. "
            f"Immediately pull the Emergency Stop Pull-Cord wire along the conveyor gallery. Cordon 15 meters around drive drum and gravity take-up counterweight."
        )
        evac_hi = (
            f"{pref_hi}पुल-कॉर्ड इमरजेंसी स्टॉप: ज़ोन {zone} में {eq_hi} में खराबी/जाम की स्थिति है। "
            f"कन्वेयर गैलरी में लगी इमरजेंसी पुल-कॉर्ड (तार) को तुरंत खींचकर मोटर बंद करें। ड्राइव ड्रम और काउंटरवेट के चारों ओर 15 मीटर का दायरा खाली रखें।"
        )
        chk_en = f"Pulled emergency stop pull-cord and cordoned 15m around {eq_en}"
        chk_hi = f"इमरजेंसी पुल-कॉर्ड खींची और 15 मीटर का सुरक्षा दायरा बनाया"

        life_en = (
            "LOTO ISOLATION & ZERO-ENERGY VERIFICATION: Apply personal padlock and danger tag to the main drive breaker. "
            "Mechanics must wear snug-fitting overalls with no loose sleeves, high-impact helmet, and steel-toe boots. Confirm complete zero-rotation before opening guards."
        )
        life_hi = (
            "LOTO तालाबंदी व शून्य-ऊर्जा पुष्टि: मेंटेनेंस से पहले मुख्य मोटर स्विच पर व्यक्तिगत LOTO ताला और डेंजर टैग लगाएं। "
            "ढीले कपड़े न पहनें, चुस्त वर्दी, हेलमेट और जूते पहनें। सुरक्षा गार्ड खोलने से पहले बेल्ट के पूरी तरह रुकने की पुष्टि करें।"
        )
        chk_life_en = "Applied LOTO lock on motor breaker and verified zero-motion"
        chk_life_hi = "मोटर स्विच पर LOTO ताला लगाया और मशीन के पूरी तरह रुकने की पुष्टि की"

        dont_en = (
            "ZERO REACH-IN ON MOVING BELTS: Absolutely FORBIDDEN to clear coal/ore buildup or apply resin using scrapers while conveyor is in motion. "
            "Never bypass pull-cord switches or defeat safety interlocks."
        )
        dont_hi = (
            "चलती मशीन में हाथ डालना पूर्ण वर्जित: चलती हुई कन्वेयर बेल्ट या ड्रम से मलबा/कोयला हाथ या लोहे की रॉड से साफ करने की कोशिश कड़ा मना है। "
            "पुल-कॉर्ड स्विच या इंटरलॉक को कभी भी बाईपास न करें।"
        )
        chk_dont_en = "Prohibited manual cleaning of moving conveyor components"
        chk_dont_hi = "चलती बेल्ट में हाथ या औजार डालने पर पूर्ण रोक लगाई"

        cmd_en = (
            "MECHANICAL MAINTENANCE DISPATCH: Mechanical Mill Maintenance (Ext 2100) and Central Safety Cell (Ext 3333) notified. "
            "Shift Maintenance Engineer on site for inspection."
        )
        cmd_hi = (
            "मैकेनिकल मेंटेनेंस टीम: मैकेनिकल मेंटेनेंस विभाग (2100) और प्लांट सेफ्टी सेल (3333) को सूचित किया गया। "
            "शिफ्ट इंजीनियर मौके पर निरीक्षण के लिए पहुंच रहे हैं।"
        )
        chk_cmd_en = "Coordinated with Mechanical Maintenance Control (2100)"
        chk_cmd_hi = "मैकेनिकल मेंटेनेंस (2100) और शिफ्ट इंजीनियर से संपर्क किया"

    # =========================================================================
    # 9. VEHICLE & TRAFFIC INCIDENT
    # =========================================================================
    elif cat_key == "vehicle_traffic_incident":
        evac_en = (
            f"{pref_en}TRAFFIC CONES & DIVERSION: Vehicle collision/breakdown involving {eq_en} in Zone {zone}. "
            f"Set reflective orange safety cones at 50m and 100m distances. Divert approaching heavy dumpers and torpedo cars onto bypass road."
        )
        evac_hi = (
            f"{pref_hi}ट्रैफिक डायवर्जन व सुरक्षा कोन: ज़ोन {zone} में {eq_hi} के साथ दुर्घटना हुई है। "
            f"50 मीटर और 100 मीटर की दूरी पर रिफ्लेक्टिव ऑरेंज कोन लगाएं। भारी डंपरों और टॉरपीडो कारों को तुरंत दूसरे रास्ते पर डायवर्ट करें।"
        )
        chk_en = f"Set 50m reflective cones and diverted plant traffic from {eq_en}"
        chk_hi = f"50 मीटर पर रिफ्लेक्टिव कोन लगाए और भारी वाहनों का रास्ता बदला"

        life_en = (
            "HIGH-VISIBILITY VEST & FUEL LEAK PROTOCOL: All responders must wear EN ISO 20471 Class 3 reflective vests and safety helmets with flashlights. "
            "Inspect vehicle undercarriage for diesel/hydraulic oil leaks; disconnect battery master switch immediately."
        )
        life_hi = (
            "हाई-विजिबिलिटी वेस्ट व डीजल रिसाव जांच: सभी कर्मी हाई-विजिबिलिटी रिफ्लेक्टिव वेस्ट और हेलमेट पहनें। "
            "वाहन के नीचे डीजल या हाइड्रोलिक तेल का रिसाव जांचें और बैटरी का मास्टर कट-ऑफ स्विच तुरंत बंद करें।"
        )
        chk_life_en = "Donned reflective vests and isolated vehicle battery master switch"
        chk_life_hi = "रिफ्लेक्टिव वेस्ट पहनी और वाहन की बैटरी का मेन स्विच काटा"

        dont_en = (
            "ZERO VEHICLE PROXIMITY ON BLIND TURNS: Do not park secondary response cars in the path of oncoming plant haul trucks. "
            "Strictly prohibit smoking or open flames near ruptured diesel tanks."
        )
        dont_hi = (
            "अंधे मोड़ पर वाहन न रोकें: बचाव वाहन को भारी ट्रकों के टर्निंग दायरे में न खड़ा करें। "
            "फटे हुए डीजल टैंक के पास सिगरेट या आग जलाना सख्त मना है।"
        )
        chk_dont_en = "Enforced zero-flame rule around ruptured fuel systems"
        chk_dont_hi = "डीजल रिसाव के पास आग जलाने या गलत पार्किंग पर रोक लगाई"

        cmd_en = (
            "PLANT TRAFFIC & SECURITY COMMAND: Plant Traffic Police / CISF (Ext 2500) and Central Medical Ambulance (Ext 102) dispatched. "
            "Heavy recovery crane mobilized."
        )
        cmd_hi = (
            "प्लांट ट्रैफिक व सुरक्षा कमांड: प्लांट सीआईएसएफ/ट्रैफिक कंट्रोल (2500) और मेडिकल एम्बुलेंस (102) को तैनात किया गया। "
            "हैवी रिकवरी क्रेन मौके के लिए रवाना।"
        )
        chk_cmd_en = "Coordinated with CISF Plant Traffic (2500) and Ambulance (102)"
        chk_cmd_hi = "सीआईएसएफ ट्रैफिक कंट्रोल (2500) और एम्बुलेंस (102) को सूचित किया"

    # =========================================================================
    # 10. SLIP, FALL & HOUSEKEEPING
    # =========================================================================
    elif cat_key == "slip_fall":
        evac_en = (
            f"{pref_en}FALL HAZARD BARRICADE: Elevated platform / walkway hazard on {eq_en} in Zone {zone}. "
            f"Barricade missing gratings, open floor holes, or greasy steps with yellow hazard tape. Cordon ground below if tools or debris could fall."
        )
        evac_hi = (
            f"{pref_hi}फॉल हैजर्ड बैरिकेड: ज़ोन {zone} में {eq_hi} पर फिसलन/ऊंचाई से गिरने का खतरा है। "
            f"खुली जाली, तेल वाले फर्श या टूटी सीढ़ियों को पीले हैजर्ड टेप से तुरंत घेरें। नीचे की जमीन पर भी घेरा बनाएं ताकि ऊपर से सामान न गिरे।"
        )
        chk_en = f"Barricaded fall hazard area and marked slippery floor on {eq_en}"
        chk_hi = f"खतरनाक सीढ़ियों/फर्श पर पीला टेप लगाकर घेराबंदी की"

        life_en = (
            "FALL ARREST HARNESS & CLEANUP: Anyone working above 1.8 meters MUST wear a full-body harness anchored to 100% tie-off lifeline. "
            "Spread absorbent sawdust or degreaser immediately on oil slicks. Wear slip-resistant steel-toe safety boots."
        )
        life_hi = (
            "सेफ्टी हार्नेस व फिसलन सफाई: 1.8 मीटर से ऊपर काम करने वाले सभी कर्मी 100% टाई-ऑफ लाइफलाइन से बंधी फुल-बॉडी हार्नेस पहनें। "
            "तेल या ग्रीस पर तुरंत सूखा बुरादा या डिग्रेसर डालें। फिसलन-रोधी सोल वाले सेफ्टी जूते पहनें।"
        )
        chk_life_en = "Inspected full-body fall arrest harness and applied floor absorbent"
        chk_life_hi = "फुल-बॉडी हार्नेस की जांच की और फर्श पर बुरादा डालकर फिसलन रोकी"

        dont_en = (
            "NO IMPROVISED LADDERS: Strictly forbidden to stand on oil drums, conveyor frames, or makeshift scaffolding. "
            "Never step on unbolted floor gratings or damaged toe-boards."
        )
        dont_hi = (
            "अस्थाई ड्रम या बेल्ट पर खड़े न हों: तेल के ड्रमों, पाइपों या बेल्ट के स्ट्रक्चर पर चढ़कर काम करना कड़ा मना है। "
            "बिना नट-बोल्ट वाली ढीली जाली पर कभी पैर न रखें।"
        )
        chk_dont_en = "Prohibited use of makeshift ladders and unsecured gratings"
        chk_dont_hi = "अस्थाई मचान या ढीली जाली पर पैर रखने पर पूर्ण रोक लगाई"

        cmd_en = (
            "PLANT SAFETY & FIRST AID COMMAND: Bokaro First Aid Station (Ext 102) and Area Housekeeping Supervisor (Ext 2100) notified. "
            "Safety inspector reviewing floor integrity."
        )
        cmd_hi = (
            "प्लांट फर्स्ट-एड व मेंटेनेंस कमांड: प्लांट प्राथमिक चिकित्सा केंद्र (102) और एरिया सुपरवाइजर (2100) को सूचित किया गया। "
            "सुरक्षा अधिकारी फर्श की मजबूती का मुआयना कर रहे हैं।"
        )
        chk_cmd_en = "Coordinated with Plant First Aid (102) and Area Supervisor"
        chk_cmd_hi = "प्राथमिक चिकित्सा (102) और एरिया सुपरवाइजर को सूचित किया"

    # =========================================================================
    # 11. PPE VIOLATION OR DEFAULT
    # =========================================================================
    else:
        evac_en = (
            f"{pref_en}MANDATORY PPE ENFORCEMENT & ACCESS CONTROL: Safety protocol breach on {eq_en} in Zone {zone}. "
            f"Restrict area entry strictly to personnel equipped with compliant safety equipment. Enforce 15-meter buffer from hazardous operations."
        )
        evac_hi = (
            f"{pref_hi}अनिवार्य PPE अनुपालन व प्रवेश नियंत्रण: ज़ोन {zone} में {eq_hi} पर सुरक्षा मानकों की स्थिति है। "
            f"केवल पूरे सुरक्षा उपकरण (PPE) पहने कर्मियों को ही कार्य क्षेत्र में जाने दें। जोखिम वाले उपकरणों से 15 मीटर की दूरी बनाए रखें।"
        )
        chk_en = f"Established 15m compliance perimeter around {eq_en}"
        chk_hi = f"{eq_hi} के आसपास 15 मीटर का सुरक्षा अनुपालन दायरा स्थापित किया"

        life_en = (
            "FULL 5-POINT INDUSTRIAL PPE INSPECTION: All workers on site must wear high-impact safety helmet with fastened chin strap, "
            "dielectric steel-toe boots, shatterproof safety goggles, cut-resistant Kevlar gloves, and high-visibility vest."
        )
        life_hi = (
            "5-पॉइंट अनिवार्य सुरक्षा गियर (PPE) जांच: कार्यस्थल पर मौजूद सभी कर्मचारी चिन-स्ट्रैप सहित हेलमेट, "
            "स्टील-टो जूते, सुरक्षा चश्मा, कट-रोधी दस्ताने और हाई-विजिबिलिटी वेस्ट अनिवार्य रूप से पहनें।"
        )
        chk_life_en = "Verified 5-point mandatory PPE on all present personnel"
        chk_life_hi = "सभी कर्मियों के हेलमेट, जूते, चश्मा व दस्तानों की जांच की"

        dont_en = (
            f"ZERO-TOLERANCE PPE VIOLATION POLICY: Strictly prohibit non-compliant workers from operating machinery or entering active shop floors. "
            "Do not lend damaged or expired helmets, cracked face shields, or torn dielectric gloves."
        )
        dont_hi = (
            "बिना PPE काम करने पर पूर्ण रोक: बिना हेलमेट या आवश्यक गियर के किसी भी व्यक्ति को मशीन चलाने या काम करने की अनुमति न दें। "
            "टूटा हुआ हेलमेट, फटा चश्मा या घिसे हुए दस्ताने कभी इस्तेमाल न करें।"
        )
        chk_dont_en = "Prohibited operation without verified safety equipment"
        chk_dont_hi = "बिना सुरक्षा उपकरण के कार्य करने पर सख्त पाबंदी लगाई"

        cmd_en = (
            "DEPARTMENTAL SAFETY CELL: Bokaro Central Safety Cell (Ext 3333) and Shift Safety Marshal (Ext 2100) notified. "
            "Issuing required safety equipment from plant safety store."
        )
        cmd_hi = (
            "विभागीय सुरक्षा सेल: बोकारो सेंट्रल सेफ्टी सेल (3333) और शिफ्ट सुरक्षा मार्शल (2100) को सूचित किया गया। "
            "प्लांट स्टोर से तुरंत आवश्यक सुरक्षा उपकरण जारी कराए जा रहे हैं।"
        )
        chk_cmd_en = "Notified Central Safety Cell (3333) and Shift Safety Marshal"
        chk_cmd_hi = "सेफ्टी सेल (3333) और सुरक्षा मार्शल को सूचित किया"

    # Assemble raw triplets
    raw_triplets = [
        ("evacuate", "🏃", evac_en, evac_hi, chk_en, chk_hi),
        ("life_safety_ppe", "🛡️", life_en, life_hi, chk_life_en, chk_life_hi),
        ("donts", "⛔", dont_en, dont_hi, chk_dont_en, chk_dont_hi),
        ("emergency_contacts", "📞", cmd_en, cmd_hi, chk_cmd_en, chk_cmd_hi),
    ]

    items = []
    for m_id, icon, t_en, t_hi, c_en, c_hi in raw_triplets:
        title_en = LOCALIZED_MEASURE_TITLES.get(m_id, {}).get("en", m_id.title())
        title_nat = LOCALIZED_MEASURE_TITLES.get(m_id, {}).get(lang, title_en)

        if lang == "en":
            text_nat = t_en
            chk_nat = c_en
        elif lang == "hi":
            text_nat = t_hi
            chk_nat = c_hi
        elif lang == "bn":
            text_nat = translation.from_english(t_en, "bn") or t_en
            chk_nat = translation.from_english(c_en, "bn") or c_en
        else:
            trans_t = translation.from_english(t_en, lang)
            text_nat = trans_t if trans_t and trans_t != t_en else t_hi
            trans_c = translation.from_english(c_en, lang)
            chk_nat = trans_c if trans_c and trans_c != c_en else c_hi

        items.append({
            "id": m_id,
            "icon": icon,
            "title": title_en,
            "title_native": title_nat,
            "text": t_en,
            "text_native": text_nat,
            "checklist_label": c_en,
            "checklist_label_native": chk_nat,
        })

    # Spoken Audio Summaries
    people_str_en = f"with {people} workers reported in the danger area" if people else "with verified active risk"
    people_str_hi = f"{people} कर्मचारियों की मौजूदगी और" if people else ""

    spoken_en = (
        f"Worker Safety Precautionary Briefing for Zone {zone}: Regarding {eq_en} {people_str_en}. "
        f"First, enforce designated exclusion perimeter. Second, ensure targeted life-safety gear. "
        f"Third, strictly adhere to critical prohibitions. Emergency response teams have been dispatched."
    )
    spoken_hi = (
        f"बोकारो सुरक्षा निर्देश: ज़ोन {zone} में {eq_hi} की घटना में {people_str_hi} आपके सत्यापन के आधार पर: "
        f"पहला, तुरंत सुरक्षा घेरा खाली करें। दूसरा, आवश्यक सुरक्षा उपकरण पहनें। "
        f"तीसरा, गलत कदम जैसे पानी डालना या मशीन चालू करना बंद रखें। आपातकालीन सहायता 101 और 102 को सतर्क किया गया है।"
    )

    return items, spoken_en, spoken_hi


def generate_precautionary_measures(ticket: Ticket) -> dict[str, Any]:
    """
    Main entry point for generating precautionary measures for an incident ticket.
    Conditions dynamically on ticket category, verified findings, situation facts, zone, and language.
    Returns prompt question, audio URL, spoken summary, and 4 grounded checklist measures.
    """
    category = ticket.predicted_category or "gas_leak"
    lang = ticket.language or "en"
    normalized_cat = normalize_category(category)
    sop_info = CATEGORY_SOP_SOURCES.get(normalized_cat, DEFAULT_SOP_SOURCE)

    # 1. Extract dynamic situational facts from incident description and verification answers
    sit = extract_situation_facts(ticket)

    # 2. Localized Prompt Question
    prompt_q = PROMPT_QUESTION_LOCALIZED.get(lang, PROMPT_QUESTION_LOCALIZED["en"])

    # 3. Build the 4 Situation-Conditioned Measures
    measures, spoken_en, spoken_hi = build_situation_measures(category, sit, lang=lang)

    # 4. Spoken Audio Summary
    spoken_native = spoken_en if lang == "en" else spoken_hi
    if lang not in ["en", "hi"]:
        trans_sp = translation.from_english(spoken_en, lang)
        spoken_native = trans_sp if trans_sp and trans_sp != spoken_en else spoken_hi

    # Synthesize smooth neural audio for prompt question & spoken summary
    q_audio_path = None
    sp_audio_path = None
    try:
        q_audio_path = tts.synthesize(prompt_q, lang)
    except Exception as exc:
        logger.warning(f"Failed to synthesize prompt question TTS for lang {lang}: {exc}")

    try:
        sp_audio_path = tts.synthesize(spoken_native, lang)
    except Exception as exc:
        logger.warning(f"Failed to synthesize precautionary measures spoken summary TTS for lang {lang}: {exc}")

    audio_url = f"/audio/{Path(sp_audio_path).name}" if sp_audio_path else None
    q_audio_url = f"/audio/{Path(q_audio_path).name}" if q_audio_path else None

    result = {
        "category": category,
        "sop_source": sop_info["title"],
        "sop_code": sop_info["code"],
        "prompt_question": PROMPT_QUESTION_LOCALIZED["en"],
        "prompt_question_native": prompt_q,
        "spoken_summary_en": spoken_en,
        "spoken_summary_native": spoken_native,
        "audio_path": audio_url,
        "question_audio_path": q_audio_url,
        "spoken_audio_path": audio_url,
        "measures": measures,
        "situation_facts": sit,
    }

    return result
