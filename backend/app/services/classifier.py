"""
Incident classifier: hybrid semantic-embedding + multilingual keyword scoring.
Grounded in Bokaro Steel Limited (BSL) plant safety categories and domain vocabulary.
Supports English, Hindi Devanagari, and Hinglish transliterations.
"""

from __future__ import annotations

from app.services import embeddings

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "fire": [
        "fire", "flame", "flames", "smoke", "burning", "blaze", "ignited", "combustion", "explosion",
        "fire extinguisher", "truck fire", "engine fire", "vehicle fire", "cable fire", "blazing",
        "आग", "आग लग", "आग लगी", "अग्नि", "धुआं", "धुआँ", "लपटें", "ज्वाला", "जल रहा", "जल गया",
        "धधक", "अंगारे", "ट्रक में आग", "गाड़ी में आग", "तरक में आग", "आग लग गई",
        "aag", "aag lagi", "dhuan", "dhuaan", "jal raha", "lapte", "fire laga",
    ],
    "gas_leak": [
        "gas", "smell", "leaking", "leak", "fumes", "odor", "hissing", "co gas", "carbon monoxide",
        "blast furnace gas", "coke oven gas", "bf gas", "pipeline leak", "valve leak", "gas holder",
        "toxic vapor", "suffocation", "rotten eggs",
        "गैस", "रिसाव", "गैस रिसाव", "लीक", "बदबू", "गंध", "हिसिंग", "कार्बन मोनोऑक्साइड",
        "जहरीली गैस", "वाल्व लीक", "पाइपलाइन रिसाव", "गैस की बदबू",
        "gas leak", "gas risav", "badboo", "gandh", "dam ghut",
    ],
    "electrical_hazard": [
        "electric", "electrical", "shock", "spark", "sparking", "short circuit", "wiring",
        "live wire", "exposed wire", "cable", "switchgear", "transformer", "breaker", "panel", "arc flash", "electrocution",
        "बिजली", "शॉर्ट सर्किट", "सर्किट", "झटका", "करंट", "स्पार्क", "चिंगारी", "बिजली का तार", "केबल",
        "ट्रांसफार्मर", "स्विचगियर", "विद्युत झटका", "पैनल स्पार्क", "चोट सरकेत", "शॉर्ट",
        "bijli", "short circuit", "chot circuit", "current", "jhatka", "chingari",
    ],
    "mechanical_failure": [
        "machine", "equipment", "jammed", "malfunction", "vibration", "broke down", "seized",
        "conveyor", "belt snapped", "roller stuck", "gearbox", "bearing", "motor tripped",
        "hydraulic failure", "coupling sheared", "shaft broken",
        "मशीन", "उपकरण", "जाम", "जाम हो गया", "खराब", "कन्वेयर बेल्ट", "बेयरिंग", "कंपन",
        "वाइब्रेशन", "मोटर ट्रिप", "हाइड्रोलिक", "टूट गया",
        "machine jam", "conveyor toot gaya", "bearing jam", "awaz aa rahi",
    ],
    "slip_fall": [
        "slip", "slipped", "fell", "fall", "tripped", "wet floor", "oil spill on floor", "uneven ground",
        "fall from height", "scaffold fall", "ladder slip", "stumble", "head injury",
        "फिसल", "फिसल गया", "पैर फिसला", "गिर पड़ा", "गिर गया", "ऊंचाई से गिरा", "गीला फर्श",
        "तेल फर्श पर", "सीढ़ी से फिसला", "चोट लग गई",
        "fisal gaya", "gir pada", "chot lag gayi", "geela farsh",
    ],
    "ppe_violation": [
        "ppe", "helmet", "without mask", "no gloves", "not wearing", "no goggles", "safety shoes",
        "face shield", "safety harness", "without helmet", "protective gear missing",
        "पीपीई", "हेलमेट नहीं", "बिना हेलमेट", "दस्ताने नहीं", "चश्मा नहीं", "सुरक्षा जूते",
        "सुरक्षा बेल्ट नहीं", "मास्क नहीं", "बिना पीपीई",
        "bina helmet", "gloves nahi", "shoes nahi", "ppe nahi pehna",
    ],
    "molten_metal_spill": [
        "molten", "hot metal", "ladle", "furnace tapping", "runner", "tap hole", "liquid steel",
        "slag", "overflow", "metal splash", "tundish", "caster breakout", "torpedo ladle",
        "पिघला", "पिघला लोहा", "पिघला हुआ धातु", "हॉट मेटल", "तरल लोहा", "लैडल", "टंडिश",
        "भट्ठी", "स्लैग", "छलक गया", "छलकना", "धातु गिर गया",
        "pighla loha", "hot metal", "ladle overflow", "chhalak gaya",
    ],
    "confined_space_emergency": [
        "confined space", "trapped inside", "collapsed inside", "vessel", "pit", "inside the tank",
        "manhole", "storage vessel", "duct", "unresponsive worker", "oxygen deficiency", "asphyxiation",
        "सीमित स्थान", "टैंक के अंदर", "अंदर फंसा", "गड्ढे में", "गड्ढा", "बेहोश हो गया",
        "दम घुट रहा", "ऑक्सीजन की कमी", "निकल नहीं पा रहा",
        "tank ke andar", "gaddhe me", "phansa hua", "behoshi",
    ],
    "crane_lifting_failure": [
        "crane", "cran", "load", "lifting", "hook", "suspended load", "dropped load", "sling", "wire rope",
        "rope snapped", "eot crane", "gantry", "hoist", "unbalanced load", "load fell",
        "क्रेन", "हुक", "लोड गिरा", "नीचे गिरा", "भार गिरा", "तार टूट", "रस्सी टूट", "झूलता हुआ लोड",
        "क्रेन का लोड", "क्रेन का तार", "क्रेन ब्रेक फेल",
        "crane", "load gir gaya", "taar toot gaya", "hook khul gaya",
    ],
    "vehicle_traffic_incident": [
        "vehicle collision", "truck collision", "wagon derailment", "locomotive collision",
        "forklift collision", "hit by", "run over", "rail track accident", "road crash",
        "heavy dumper accident", "brake failure collision", "traffic accident",
        "टक्कर", "गाड़ी टकराई", "ट्रक टक्कर", "डंपर टक्कर", "वैगन पटरी से उतरी", "लोकोमोटिव टक्कर",
        "फोर्कलिफ्ट टक्कर", "धक्का लगा", "कुचल गया", "रेल ट्रैक दुर्घटना",
        "takkar", "gaadi takrai", "dumper takkar", "loco takkar", "accident ho gaya",
    ],
    "chemical_spill": [
        "chemical", "acid", "corrosive", "solvent", "spilled", "hydrochloric acid", "hcl",
        "sulfuric acid", "caustic soda", "chemical burn", "acid splash", "battery leak",
        "रसायन", "एसिड", "तेजाब", "हाइड्रोक्लोरिक", "सल्फ्यूरिक", "एसिड रिसाव", "एसिड छलक गया",
        "केमिकल गिरा", "ज्वलनशील रसायन",
        "acid leak", "acid gir gaya", "tezab", "rasayanik",
    ],
}

CATEGORY_PROFILES: dict[str, str] = {
    "gas_leak": (
        "A toxic, flammable, or hazardous gas leak or gas smell in plant areas such as blast furnace gas lines, "
        "coke oven gas, carbon monoxide (CO), gas holder stations, piping flanges, valves, or regulators. "
        "Symptoms include hissing sound, foul or rotten odor, dizziness, headache, or workers feeling suffocated."
    ),
    "fire": (
        "An active fire, blaze, combustion, or smoke outbreak in the plant, including industrial building fires, "
        "cable tunnel fires, conveyor fires, overheated motors, or engine fires in heavy plant vehicles like trucks and dumpers. "
        "Characterized by visible flames, heavy black or white smoke, burning smell, intense radiant heat, or glowing embers."
    ),
    "electrical_hazard": (
        "An electrical emergency involving live energized equipment, high voltage switchgear, transformers, motor control centers, "
        "substations, short circuits, arc flashes, exposed wiring, electrical sparking, panel fires, or worker receiving electric shock."
    ),
    "mechanical_failure": (
        "Mechanical breakdown, seizure, or malfunction of plant machinery such as conveyor belts jamming or snapping, "
        "gearboxes failing, pump or compressor breakdowns, severe abnormal vibration, bearing overheating, or hydraulic system failure."
    ),
    "slip_fall": (
        "A worker slip, trip, loss of balance, or physical fall resulting from slippery wet floors, grease or oil on walkways, "
        "tripping hazards, uneven industrial gratings, falling from ladders, scaffolding, or elevated steel platforms."
    ),
    "ppe_violation": (
        "Safety compliance violation where personnel are working without mandatory personal protective equipment, "
        "such as failure to wear hard hat safety helmets, safety shoes, flame-retardant clothing, eye goggles, ear defenders, or fall harness."
    ),
    "molten_metal_spill": (
        "Catastrophic or hazardous spill, overflow, splashing, or breakout of molten iron, liquid steel, or hot slag "
        "from blast furnace tap holes, torpedo ladles, steel melting shop converters, tundishes, or continuous casting machines."
    ),
    "confined_space_emergency": (
        "Emergency involving workers inside enclosed or restricted spaces such as storage tanks, vessels, gas ducts, "
        "furnace interiors, sewers, manholes, or subterranean valve pits where there is oxygen deficiency, toxic atmosphere, or worker trapped."
    ),
    "crane_lifting_failure": (
        "Failure of overhead EOT cranes, mobile cranes, hoists, slings, or rigging equipment where a heavy suspended load "
        "drops, slips from the hook, wire rope snaps, brake fails, or the swinging load strikes nearby plant structures or workers."
    ),
    "vehicle_traffic_incident": (
        "Traffic collisions, crashes, or moving vehicle accidents within plant roads and rail yards, involving heavy haul trucks, "
        "in-plant dumpers, slag pot carriers, forklifts, locomotives, or rail wagons colliding with other vehicles, structures, or pedestrians."
    ),
    "chemical_spill": (
        "Uncontrolled release, splashing, rupture, or spill of hazardous chemicals or corrosive liquids such as hydrochloric acid (HCl), "
        "sulfuric acid, caustic lye, pickling liquor, solvents, or water treatment reagents presenting chemical burn and toxic inhalation hazards."
    ),
}

_CATEGORY_ORDER = list(CATEGORY_PROFILES.keys())
_profile_embeddings = None


def _get_profile_embeddings():
    global _profile_embeddings
    if _profile_embeddings is None:
        _profile_embeddings = embeddings.encode([CATEGORY_PROFILES[c] for c in _CATEGORY_ORDER])
    return _profile_embeddings


def _keyword_score(text: str, category: str) -> int:
    lowered = text.lower()
    return sum(1 for kw in CATEGORY_KEYWORDS[category] if kw in lowered)


def classify(text: str, language: str = "en", raw_text: str | None = None) -> tuple[str | None, float]:
    combined_text = f"{text} {raw_text or ''}".strip()
    if not combined_text:
        return None, 0.0

    # If the text passed for embedding is non-Latin (e.g. raw Hindi), translate to English for semantic matching
    text_for_embedding = text
    if any(ord(c) > 127 for c in text):
        try:
            from app.services import translation
            text_for_embedding = translation.to_english(text, "hi") or text
        except Exception:
            text_for_embedding = text

    profile_vecs = _get_profile_embeddings()
    text_vec = embeddings.encode([text_for_embedding])[0]
    similarities = profile_vecs @ text_vec  # cosine similarity, both sides normalized

    scores = {}
    for i, category in enumerate(_CATEGORY_ORDER):
        keyword_hits = _keyword_score(combined_text, category)
        scores[category] = float(similarities[i]) + 0.08 * keyword_hits

    best_category = max(scores, key=lambda c: scores[c])
    best_score = scores[best_category]

    confidence = round(min(0.95, max(0.20, best_score)), 2)
    return best_category, confidence


if __name__ == "__main__":
    test_cases = [
        ("The area near the panel is extremely hot and I can see it glowing red, there's a crackling sound", None, "fire"),
        ("The conveyor belt drive shuddered violently and then locked in place, it will not turn now", None, "mechanical_failure"),
        ("My colleague went down into the storage container an hour ago and isn't responding when we call him", None, "confined_space_emergency"),
        ("I smell gas near the gas holder station, not sure how strong it is", None, "gas_leak"),
        ("In the truck, there is fire in the truck. What should I do?", "तरक में आग, गाड़ी है, में क्या कर।", "fire"),
        ("I have a short circuit that is taking place in the smoke oven.", "मुछे, चोट लिएक, अचाद सरकेत होता होटिवा इवही दिर हा है, कोक हुद में", "electrical_hazard"),
        ("ट्रक में आग लग गई है, मैं क्या करूँ?", "truck mein aag lag gayi hai", "fire"),
    ]
    for text, raw, expected in test_cases:
        category, confidence = classify(text, raw_text=raw)
        status = "OK" if category == expected else "MISMATCH"
        print(f"[{status}] text={text!r} raw={raw!r} -> ({category}, {confidence}) expected={expected}")
