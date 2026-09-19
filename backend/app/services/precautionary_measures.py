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
    if "fire" in cat or "flame" in cat:
        return "fire"
    if "elec" in cat:
        return "electrical_hazard"
    if "molten" in cat or "metal" in cat:
        return "molten_metal_spill"
    if "chem" in cat or "acid" in cat:
        return "chemical_spill"
    if "confined" in cat or "space" in cat:
        return "confined_space_emergency"
    if "crane" in cat or "lift" in cat or "rigging" in cat:
        return "crane_lifting_failure"
    if "conveyor" in cat or "belt" in cat or "mech" in cat or "machine" in cat:
        return "mechanical_failure"
    if "slip" in cat or "fall" in cat or "trip" in cat:
        return "slip_fall"
    if "vehicle" in cat or "traffic" in cat or "truck" in cat or "collision" in cat:
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
    desc_en = ticket.incident_description_en or ""
    desc_nat = ticket.incident_description or ""

    combined_en = f"{desc_en} " + " ".join(answers_en)
    combined_nat = f"{desc_nat} " + " ".join(answers_nat)
    text_en_low = combined_en.lower()

    # 1. Concrete Equipment Identification
    eq_name = "Plant Equipment / Facility"
    eq_name_hi = "संयंत्र उपकरण / स्थल"
    if any(w in text_en_low or w in combined_nat for w in ["crane", "क्रेन"]):
        eq_name = "Overhead EOT Crane & Gantry Runway"
        eq_name_hi = "ओवरहेड ईओटी क्रेन एवं गैन्ट्री रनवे"
    elif any(w in text_en_low or w in combined_nat for w in ["truck", "dumper", "ट्रक", "डंपर"]):
        eq_name = "Heavy Transport Truck / Dumper Engine"
        eq_name_hi = "भारी परिवहन ट्रक / डंपर इंजन"
    elif any(w in text_en_low or w in combined_nat for w in ["live wire", "wire", "cable", "switchgear", "बिजली", "तार", "केबल"]):
        eq_name = "High-Voltage Electrical Cable & Switchgear"
        eq_name_hi = "हाई-वोल्टेज इलेक्ट्रिकल केबल एवं स्विचगियर"
    elif any(w in text_en_low or w in combined_nat for w in ["valve", "pipeline", "flange", "वाल्व", "पाइपलाइन"]):
        eq_name = "Gas Distribution Pipeline & Isolation Valve"
        eq_name_hi = "गैस वितरण पाइपलाइन एवं आइसोलेशन वाल्व"
    elif any(w in text_en_low or w in combined_nat for w in ["ladle", "tundish", "furnace", "लैडल", "भट्ठी"]):
        eq_name = "Liquid Metal Ladle & Furnace Casthouse"
        eq_name_hi = "तरल धातु लैडल एवं ब्लास्ट फर्नेस कास्टहाउस"
    elif any(w in text_en_low or w in combined_nat for w in ["tank", "pit", "vessel", "टैंक", "गड्ढा"]):
        eq_name = "Confined Storage Tank & Underground Pit"
        eq_name_hi = "सीमित भंडारण टैंक एवं भूमिगत गड्ढा"
    elif any(w in text_en_low or w in combined_nat for w in ["acid", "chemical", "hcl", "एसिड", "तेजाब"]):
        eq_name = "Acid Storage Tank & Pickling Line"
        eq_name_hi = "एसिड भंडारण टैंक एवं केमिकल पिकलिंग लाइन"
    elif any(w in text_en_low or w in combined_nat for w in ["conveyor", "belt", "कन्वेयर"]):
        eq_name = "Raw Material Conveyor Belt Drive"
        eq_name_hi = "रॉ मटेरियल कन्वेयर बेल्ट ड्राइव"

    # 2. Number of personnel in danger / vicinity
    people_count = None
    num_match = re.search(
        r"\b(one|two|three|four|five|six|seven|eight|nine|ten|\d+)\s*(people|workers|persons|men|लोग|कर्मचारी)?\b",
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

    # 3. Spread dynamics & smoke severity
    is_spreading = any(
        w in text_en_low or w in combined_nat
        for w in ["fast", "rapid", "spreading", "heavy smoke", "dense", "out of control", "तेज", "तेजी", "फैल", "धुआं फैल", "धुआ बहल"]
    )

    # 4. Shock victim contact
    has_shock_victim = any(
        w in text_en_low or w in combined_nat
        for w in ["stuck", "struck", "shock", "victim in contact", "direct contact", "electrocution", "power blow", "झटका लगा", "करंट लगा", "चिपक", "बिजली लगी", "आदमी गिरा", "बेहोश"]
    )

    # 5. Breaker / LOTO status
    loto_tripped = any(
        w in text_en_low or w in combined_nat
        for w in ["tripped", "locked out", "loto", "power cut", "switched off", "power off", "breaker", "ब्रेकर ट्रिप", "बंद कर दिया", "मेन स्विच", "बिजली काट", "स्विच बंद"]
    )

    # 6. Manual suppression / extinguisher status
    uncontrolled = any(
        w in text_en_low or w in combined_nat
        for w in ["no", "cannot", "not available", "uncontrolled", "failed", "नहीं", "नहीं बुझा", "काबू नहीं", "बेकाबू", "आग ज्यादा"]
    )

    # 7. Symptoms
    has_symptoms = any(
        w in text_en_low or w in combined_nat
        for w in ["dizzy", "dizziness", "choking", "breath", "unconscious", "चक्कर", "दम घुटना", "बेहोश"]
    )

    return {
        "equipment_en": eq_name,
        "equipment_hi": eq_name_hi,
        "people_count": people_count,
        "is_spreading": is_spreading,
        "has_shock_victim": has_shock_victim,
        "loto_tripped": loto_tripped,
        "uncontrolled": uncontrolled,
        "has_symptoms": has_symptoms,
        "zone": ticket.zone_id or "Incident Area",
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
    loto = sit["loto_tripped"]

    # -------------------------------------------------------------------------
    # MEASURE 1: Situation-Specific Evacuation & Exclusion Zone
    # -------------------------------------------------------------------------
    if cat_key == "fire":
        if "crane" in eq_en.lower():
            evac_en = (
                f"IMMEDIATE 30-METER DROP ZONE CORDON: Fire is active on {eq_en} in Zone {zone}. "
                f"Falling burning debris and hydraulic oil pose an extreme hazard. Clear a 30-meter ground radius below the gantry immediately. "
            )
            evac_hi = (
                f"30 मीटर क्रेन डेंजर ज़ोन खाली करें: ज़ोन {zone} में {eq_hi} में आग सक्रिय है। "
                f"जलते हुए मलबे और हाइड्रोलिक तेल से बचने के लिए क्रेन गैन्ट्री के नीचे 30 मीटर का दायरा तुरंत खाली करें। "
            )
            chk_en = f"Enforced 30m drop zone perimeter under {eq_en}"
            chk_hi = f"{eq_hi} के नीचे 30 मीटर का दायरा सुरक्षित किया"
        else:
            evac_en = (
                f"IMMEDIATE EXCLUSION PERIMETER: Active fire reported on {eq_en} in Zone {zone}. "
                f"Establish a 25-meter perimeter barrier around the combustion zone immediately. "
            )
            evac_hi = (
                f"तत्काल सुरक्षा घेरा: ज़ोन {zone} में {eq_hi} में आग की सूचना मिली है। "
                f"आग के स्थल से कम से कम 25 मीटर का सुरक्षा घेरा तुरंत स्थापित करें। "
            )
            chk_en = f"Established 25m safety perimeter around {eq_en}"
            chk_hi = f"{eq_hi} के चारों ओर 25 मीटर का घेरा बनाया"

        if people:
            evac_en += f"HEADCOUNT PRIORITY: {people} workers were reported in the vicinity; guide all {people} personnel to Emergency Muster Point immediately and conduct roll-call headcount."
            evac_hi += f"कर्मचारी हाजिरी प्राथमिकता: {people} कर्मचारियों की मौजूदगी दर्ज है; सभी {people} कर्मियों को तुरंत असेंबली पॉइंट पर भेजें और हाजिरी की पुष्टि करें।"
        else:
            evac_en += "Direct all nearby plant personnel to the designated Assembly Point via marked fire exit routes."
            evac_hi += "चिन्हित अग्नि निकास मार्गों से सभी कर्मियों को सुरक्षित असेंबली पॉइंट पर भेजें।"

    elif cat_key == "electrical_hazard":
        evac_en = (
            f"10-METER STEP-POTENTIAL CLEARANCE: An energized electrical fault is reported on {eq_en} in Zone {zone}. "
            f"Establish an absolute 10-meter (33-foot) exclusion zone. Do NOT walk normally over wet floors or metal gratings—shuffle feet together to avoid fatal step-potential shock."
        )
        evac_hi = (
            f"10 मीटर स्टेप-पोटेंशियल सुरक्षित दूरी: ज़ोन {zone} में {eq_hi} पर बिजली का फॉल्ट हुआ है। "
            f"कम से कम 10 मीटर का दायरा पूरी तरह खाली कराएं। गीले फर्श या लोहे की जाली पर सामान्य रूप से न चलें—पैरों को सटाकर चलें ताकि बिजली का झटका न लगे।"
        )
        if people:
            evac_en += f" MUSTER PRIORITY: {people} workers reported nearby; ensure all {people} personnel remain outside the 10-meter ground-fault boundary."
            evac_hi += f" कर्मचारी हाजिरी प्राथमिकता: {people} कर्मचारियों की मौजूदगी दर्ज है; सभी {people} कर्मियों को बिजली क्षेत्र से 10 मीटर दूर सुरक्षित रखें।"
        chk_en = "Cordoned 10-meter step-potential zone from live electrical source"
        chk_hi = "बिजली के स्रोत से 10 मीटर का सुरक्षा घेरा बनाया"

    elif cat_key == "gas_leak":
        evac_en = (
            f"UPWIND 90-DEGREE EVACUATION: Toxic/flammable gas release from {eq_en} in Zone {zone}. "
            f"Evacuate crosswind at 90 degrees, then move upwind to elevated muster ground. Strictly avoid pits, cable trenches, or basements where heavy CO/BFG gas pools."
        )
        evac_hi = (
            f"हवा के विपरीत 90 डिग्री पर निकासी: ज़ोन {zone} में {eq_hi} से जहरीली/ज्वलनशील गैस का रिसाव हुआ है। "
            f"हवा के 90 डिग्री कोण पर सुरक्षित अपविंड ऊंचे स्थान पर जाएं। गड्ढों, केबल बेसमेंट या नालों में बिल्कुल न जाएं जहां भारी गैस जमा होती है।"
        )
        if people:
            evac_en += f" MUSTER PRIORITY: Guide all {people} workers upwind immediately and verify headcount."
            evac_hi += f" कर्मचारी हाजिरी: सभी {people} कर्मियों को तुरंत हवा के विपरीत सुरक्षित स्थान पर ले जाकर हाजिरी लें।"
        chk_en = "Evacuated all personnel crosswind/upwind away from gas cloud"
        chk_hi = "गैस रिसाव से हवा के विपरीत सुरक्षित स्थान पर पहुंचे"

    elif cat_key == "molten_metal_spill":
        evac_en = (
            f"30-METER SPLASH PERIMETER: Molten metal/slag breakout from {eq_en} in Zone {zone}. "
            f"Clear at least 30 meters radially. Move perpendicular to the liquid metal flow path towards elevated, dry concrete flooring."
        )
        evac_hi = (
            f"30 मीटर स्प्लैश दायरा खाली करें: ज़ोन {zone} में {eq_hi} से पिघली धातु/स्लैग का रिसाव हुआ है। "
            f"कम से कम 30 मीटर दूर हटें। धातु के बहाव की दिशा से लंबवत होकर सूखे और ऊंचे फर्श की ओर जाएं।"
        )
        if people:
            evac_en += f" MUSTER PRIORITY: Verify all {people} workers are clear of the 30m splash zone."
            evac_hi += f" कर्मचारी हाजिरी: पुष्टि करें कि सभी {people} कर्मी 30 मीटर के स्प्लैश दायरे से बाहर सुरक्षित हैं।"
        chk_en = "Cleared 30m molten splash zone to dry elevated flooring"
        chk_hi = "पिघली धातु से 30 मीटर दूर सूखे फर्श पर पहुंचे"

    else:
        evac_en = (
            f"INCIDENT CORDON & CLEARANCE: Hazardous condition on {eq_en} in Zone {zone}. "
            f"Maintain an exclusion perimeter of at least 25 meters. Keep all road access clear for arriving emergency vehicles."
        )
        evac_hi = (
            f"घटना स्थल की घेराबंदी: ज़ोन {zone} में {eq_hi} पर आपात स्थिति है। "
            f"कम से कम 25 मीटर की दूरी बनाए रखें। राहत वाहनों के आवागमन के लिए मुख्य रास्ता पूरी तरह खाली रखें।"
        )
        chk_en = "Established 25m cordon and cleared access road for emergency vehicles"
        chk_hi = "25 मीटर का घेरा बनाया और राहत वाहनों का रास्ता साफ रखा"

    # -------------------------------------------------------------------------
    # MEASURE 2: Targeted Life-Safety & Protective Action
    # -------------------------------------------------------------------------
    if shock_victim:
        life_en = (
            "ZERO-TOUCH RESCUE PROTOCOL: A worker is reported in contact with electricity. "
            "CRITICAL: DO NOT touch the victim with bare hands or conductive clothing. Use a certified non-conductive fiberglass rescue hook or dry wooden pole to disengage the victim. "
            f"{'Main breaker is reported tripped (LOTO applied); verify zero-voltage before physical skin contact.' if loto else 'De-energize main breaker immediately before touching victim.'} "
            "Initiate CPR immediately if breathing stops once clear."
        )
        life_hi = (
            "जीरो-टच रेस्क्यू प्रोटोकॉल: कर्मचारी बिजली के संपर्क में बताया गया है। "
            "अत्यंत महत्वपूर्ण: पीड़ित को नंगे हाथों या कपड़ों से सीधे न छुएं। केवल इंसुलेटेड फाइबरग्लास रेस्क्यू हुक या सूखी लकड़ी के डंडे से पीड़ित को अलग करें। "
            f"{'मेन ब्रेकर ट्रिप/LOTO बताया गया है; छूने से पहले शून्य वोल्टेज की पुष्टि करें।' if loto else 'पीड़ित को छूने से पहले तुरंत मेन पावर स्विच बंद करें।'} "
            "अलग होने के बाद सांस न चलने पर तुरंत सीपीआर शुरू करें।"
        )
        chk_life_en = "Rescued shock victim using non-conductive tool and initiated CPR"
        chk_life_hi = "पीड़ित को बिना छुए अलग किया और प्राथमिक उपचार शुरू किया"

    elif spreading and cat_key == "fire":
        life_en = (
            f"RESPIRATORY SMOKE PROTOCOL: Toxic combustion smoke is spreading rapidly from {eq_en}. "
            "Personnel within 25 meters must don emergency particulate smoke hoods or damp cotton cloths over nose and mouth. "
            "Stay low beneath the rising thermal ceiling. Under no circumstances climb crane access ladders or enter smoke-filled enclosures."
        )
        life_hi = (
            f"विषाक्त धुआं श्वसन सुरक्षा: {eq_hi} से घना धुआं तेजी से फैल रहा है। "
            "25 मीटर के दायरे में मौजूद कर्मी तुरंत स्मोक मास्क या गीला कपड़ा मुंह और नाक पर रखें। "
            "धुएं की चादर से नीचे झुककर चलें। धुएं के बीच क्रेन की सीढ़ियों या बंद केबिन में बिल्कुल न चढ़ें।"
        )
        chk_life_en = "Donned respiratory smoke hoods and stayed below smoke ceiling"
        chk_life_hi = "रेस्पिरेटरी मास्क पहना और धुएं से नीचे झुककर बाहर निकले"

    elif cat_key == "gas_leak":
        life_en = (
            "SCBA & ESCAPE HOOD MANDATE: Personnel entering or operating near the gas envelope MUST wear self-contained breathing apparatus (SCBA). "
            "Standard dust masks provide zero protection against toxic carbon monoxide (CO) or hydrogen sulfide. "
            "Administer 100% high-flow medical oxygen immediately to anyone experiencing dizziness or headache."
        )
        life_hi = (
            "SCBA व ऑक्सीजन जीवन-रक्षा: गैस क्षेत्र के पास जाने वाले कर्मियों के लिए सेल्फ-कंटेन्ड ब्रीदिंग उपकरण (SCBA) पहनना अनिवार्य है। "
            "साधारण मास्क जहरीली कार्बन मोनोऑक्साइड (CO) से कोई सुरक्षा नहीं देता। "
            "चक्कर या सिरदर्द महसूस करने वाले कर्मियों को तुरंत 100% मेडिकल ऑक्सीजन दें।"
        )
        chk_life_en = "Verified SCBA respiratory gear and readied emergency oxygen"
        chk_life_hi = "SCBA उपकरण की जांच की और मेडिकल ऑक्सीजन तैयार की"

    elif cat_key == "molten_metal_spill":
        life_en = (
            "ALUMINIZED SUIT & ZERO-MOISTURE CHECK: Don full heat-reflective aluminized foundry suits with cobalt-blue face shields and spats. "
            "CRITICAL: Inspect flooring in the path of liquid metal—verify NO water puddles, damp dust, or moisture exist, which triggers catastrophic steam explosions."
        )
        life_hi = (
            "एल्युमिनाइज्ड सूट व नमी-रहित जांच: गर्मी-रोधी एल्युमिनाइज्ड सूट और कोबाल्ट-ब्लू फेस शील्ड पहनें। "
            "अति महत्वपूर्ण: पिघली धातु के मार्ग में फर्श की जांच करें—पानी या नमी बिल्कुल नहीं होनी चाहिए, अन्यथा भयानक भाप विस्फोट हो सकता है।"
        )
        chk_life_en = "Inspected aluminized gear and confirmed zero water in metal flow path"
        chk_life_hi = "एल्युमिनाइज्ड सूट पहना और धातु के रास्ते में नमी न होने की पुष्टि की"

    else:
        life_en = (
            f"MANDATORY PPE INSPECTION: All workers responding near {eq_en} must wear high-impact industrial safety helmets with chin straps fastened, "
            "steel-toe dielectric footwear, high-visibility vest, and shatterproof eye protection."
        )
        life_hi = (
            f"अनिवार्य सुरक्षा उपकरण जांच: {eq_hi} के पास काम करने वाले सभी कर्मचारी चिन स्ट्रैप सहित सुरक्षा हेलमेट, "
            "स्टील-टो इंसुलेटेड जूते, हाई-विजिबिलिटी वेस्ट और सुरक्षा चश्मा अनिवार्य रूप से पहनें।"
        )
        chk_life_en = "Inspected 4-point mandatory PPE on all personnel"
        chk_life_hi = "सभी कर्मियों के सुरक्षा उपकरणों (PPE) की जांच की"

    # -------------------------------------------------------------------------
    # MEASURE 3: Critical Situation Prohibitions (Don'ts)
    # -------------------------------------------------------------------------
    if cat_key in ["fire", "electrical_hazard"]:
        dont_en = (
            f"ABSOLUTE WATER BAN ON {eq_en.upper()}: Never use water, water-mist, or conductive foam on live electrical cables, switchgear, or crane busbars. "
            "Water will conduct lethal electrical shock and trigger catastrophic arc flash explosions. "
            f"{'Manual fire suppression is unsafe; leave firefighting strictly to BSL Fire Brigade.' if sit['uncontrolled'] else 'Use only dry chemical powder (DCP) or CO2 extinguishers from at least 3 meters away once de-energized.'}"
        )
        dont_hi = (
            f"{eq_hi} पर पानी का उपयोग पूर्णतः वर्जित: बिजली के केबल, स्विचगियर या क्रेन के तारों पर कभी भी पानी या झाग न डालें। "
            "पानी से जानलेवा करंट फैल सकता है और भयानक शॉर्ट सर्किट ब्लास्ट हो सकता है। "
            f"{'आग बेकाबू है; खुद बुझाने की कोशिश न करें, केवल फायर ब्रिगेड का इंतजार करें।' if sit['uncontrolled'] else 'पावर कट होने के बाद ही कम से कम 3 मीटर की दूरी से CO2 या ड्राई केमिकल पाउडर का उपयोग करें।'}"
        )
        chk_dont_en = f"Strictly prohibited water application on {eq_en}"
        chk_dont_hi = f"{eq_hi} पर पानी का उपयोग पूरी तरह प्रतिबंधित किया"

    elif cat_key == "gas_leak":
        dont_en = (
            "IGNITION SOURCE PROHIBITION: Strictly FORBIDDEN to operate mobile phones, walkie-talkies, electrical switches, or start vehicle engines within 50 meters of the gas leak envelope. "
            "Do NOT attempt manual valve isolation without a second buddy and positive-pressure SCBA."
        )
        dont_hi = (
            "स्पार्क व मोबाइल फोन पूर्णतः प्रतिबंधित: गैस रिसाव के 50 मीटर के दायरे में मोबाइल फोन, वॉकी-टॉकी, बिजली के स्विच चालू/बंद करना या गाड़ी स्टार्ट करना सख्त मना है। "
            "बिना SCBA और सहयोगी साथी के वाल्व बंद करने की कोशिश न करें।"
        )
        chk_dont_en = "Enforced total ignition & mobile phone ban in gas envelope"
        chk_dont_hi = "गैस क्षेत्र में मोबाइल फोन व बिजली स्विच पर पूर्ण रोक लगाई"

    elif cat_key == "molten_metal_spill":
        dont_en = (
            "ZERO WATER & EXTINGUISHER RESTRICTION: Absolutely FORBIDDEN to spray water hoses or throw damp materials onto molten slag or liquid metal. "
            "Do not allow overhead cranes to travel directly over the spill until thermal dissipation is confirmed."
        )
        dont_hi = (
            "पानी का छिड़काव पूर्णतः प्रतिबंधित: पिघली धातु या स्लैग पर पानी की नली या गीली वस्तुएं फेंकना कड़ा मना है। "
            "जब तक गर्मी शांत न हो जाए, क्रेन को छलकन वाले क्षेत्र के ऊपर न ले जाएं।"
        )
        chk_dont_en = "Enforced zero-water rule on molten metal spill"
        chk_dont_hi = "पिघली धातु पर पानी न डालने के नियम का पालन कराया"

    else:
        dont_en = (
            f"UNAUTHORIZED ACCESS PROHIBITION: Strictly prohibit untrained personnel from entering the cordon around {eq_en}. "
            "Do not restart tripped machinery or re-energize breakers without formal written clearance from the Shift Safety Incharge."
        )
        dont_hi = (
            f"अनाधिकृत प्रवेश निषेध: {eq_hi} के सुरक्षा घेरे में अप्रशिक्षित कर्मियों का प्रवेश वर्जित है। "
            "शिफ्ट सुरक्षा प्रभारी की लिखित अनुमति के बिना बंद मशीन या ट्रिप हुए ब्रेकर को दोबारा चालू न करें।"
        )
        chk_dont_en = f"Prohibited unauthorized restart and entry to {eq_en}"
        chk_dont_hi = f"{eq_hi} को बिना अनुमति दोबारा चालू करने पर रोक लगाई"

    # -------------------------------------------------------------------------
    # MEASURE 4: Incident Command & Emergency Dispatches
    # -------------------------------------------------------------------------
    if cat_key == "electrical_hazard" or shock_victim:
        cmd_en = (
            "BOKARO EMERGENCY TRAUMA & ELECTRICAL COMMAND: Central Medical Emergency Trauma Ambulance (Ext 102) dispatched with automated external defibrillator (AED). "
            "Electrical Substation Control Room (Ext 3111) notified for mandatory Lockout/Tagout (LOTO) isolation. Central Safety Officer (Ext 3333) conducting incident command."
        )
        cmd_hi = (
            "बोकारो मेडिकल ट्रॉमा व इलेक्ट्रिकल कमांड: मेडिकल ट्रॉमा एम्बुलेंस (102) डिफ़िब्रिलेटर (AED) सहित मौके के लिए रवाना। "
            "इलेक्ट्रिकल सबस्टेशन (3111) को अनिवार्य LOTO पावर कट के लिए सूचित किया गया। केंद्रीय सुरक्षा अधिकारी (3333) द्वारा कमान संभाली गई।"
        )
        chk_cmd_en = "Coordinated with Bokaro Trauma Ambulance (102) and Electrical Control (3111)"
        chk_cmd_hi = "मेडिकल एम्बुलेंस (102) और इलेक्ट्रिकल कंट्रोल (3111) से समन्वय किया"

    elif cat_key == "fire":
        cmd_en = (
            f"BSL FIRE BRIGADE EMERGENCY DISPATCH: Plant Fire Services Crash Tenders (Ext 101 / 3333) dispatched to {eq_en} in Zone {zone}. "
            "Plant Medical Trauma Team (Ext 102) on standby. Area Maintenance Superintendent (Ext 2100) managing perimeter isolation."
        )
        cmd_hi = (
            f"बीएसएल फायर ब्रिगेड आपातकालीन दस्ता: प्लांट फायर सर्विसेज क्रैश टेंडर (101 / 3333) ज़ोन {zone} में {eq_hi} के लिए रवाना। "
            "मेडिकल ट्रॉमा टीम (102) स्टैंडबाय पर तैनात। शिफ्ट अधीक्षक (2100) द्वारा सुरक्षा घेरे का प्रबंधन जारी।"
        )
        chk_cmd_en = "Confirmed BSL Fire Crash Tender (101) & Medical Team (102) en route"
        chk_cmd_hi = "फायर ब्रिगेड (101) और मेडिकल टीम (102) के मौके पर पहुंचने की पुष्टि की"

    elif cat_key == "gas_leak":
        cmd_en = (
            "GAS SAFETY SQUAD & RESCUE DISPATCH: Bokaro Gas Safety Station (Ext 2222) dispatched with heavy rescue SCBA gear and gas sniffing detectors. "
            "Emergency Fire Control (Ext 101) & Medical Trauma Unit (Ext 102) placed on high alert."
        )
        cmd_hi = (
            "गैस सुरक्षा दस्ता एवं बचाव दल तैनात: बोकारो गैस सुरक्षा स्टेशन (2222) SCBA गियर और गैस डिटेक्टर के साथ रवाना। "
            "फायर कंट्रोल (101) और मेडिकल ट्रॉमा यूनिट (102) को हाई अलर्ट पर रखा गया।"
        )
        chk_cmd_en = "Confirmed Bokaro Gas Safety Squad (2222) dispatched"
        chk_cmd_hi = "गैस सुरक्षा दस्ते (2222) के पहुंचने की पुष्टि की"

    else:
        cmd_en = (
            "CENTRAL SAFETY ESCALATION: Bokaro Plant Safety Cell (Ext 3333) and Central Emergency Control (Ext 101) notified. "
            "Shift Maintenance Supervisor (Ext 2100) and Plant Ambulance (Ext 102) dispatched to incident location."
        )
        cmd_hi = (
            "केंद्रीय सुरक्षा नियंत्रण: बोकारो प्लांट सेफ्टी सेल (3333) और सेंट्रल इमरजेंसी कंट्रोल (101) को सूचित किया गया। "
            "शिफ्ट मेंटेनेंस सुपरवाइजर (2100) और प्लांट एम्बुलेंस (102) घटना स्थल के लिए रवाना।"
        )
        chk_cmd_en = "Notified Central Safety Cell (3333) and Shift Supervisor (2100)"
        chk_cmd_hi = "सेफ्टी सेल (3333) और शिफ्ट सुपरवाइजर (2100) को सूचित किया"

    # Assemble raw items
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
    people_str_en = f"with {people} workers reported in the danger area" if people else "with active hazard in area"
    people_str_hi = f"{people} कर्मचारियों की मौजूदगी को देखते हुए" if people else "खतरे को देखते हुए"

    spoken_en = (
        f"Worker Safety Precautionary Directives for Zone {zone}: Emergency on {eq_en} {people_str_en}. "
        f"Immediately enforce the designated exclusion perimeter. Comply with specialized protective gear rules. "
        f"Strictly avoid prohibited actions like using water on electrical hazards. Bokaro Emergency Control is on 101."
    )
    spoken_hi = (
        f"बोकारो सुरक्षा निर्देश: ज़ोन {zone} में {eq_hi} में दुर्घटना हुई है, {people_str_hi}। "
        f"तुरंत सुरक्षा दायरा खाली करें। आवश्यक सुरक्षा उपकरण पहनें। पानी के गलत उपयोग या अनधिकृत प्रवेश से बचें। "
        f"फायर ब्रिगेड 101 और मेडिकल इमरजेंसी 102 को रवाना किया गया है।"
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

    result = {
        "category": category,
        "sop_source": sop_info["title"],
        "sop_code": sop_info["code"],
        "prompt_question": PROMPT_QUESTION_LOCALIZED["en"],
        "prompt_question_native": prompt_q,
        "spoken_summary_en": spoken_en,
        "spoken_summary_native": spoken_native,
        "audio_path": sp_audio_path,
        "question_audio_path": q_audio_path,
        "spoken_audio_path": sp_audio_path,
        "measures": measures,
        "situation_facts": sit,
    }

    return result
