"""
Heavy Industry Plant Floor Vernacular Glossary and Domain Lexicon.
Maps informal, Hinglish, Hindi, and colloquial jargon used by steel plant workers
to standard safety concepts and search anchor terms for hybrid RAG retrieval.
"""

from typing import Any

# Plant Glossary & Vernacular Synonym Lexicon
DOMAIN_GLOSSARY: dict[str, list[str]] = {
    # Gas terms
    "gas_leak": [
        "gas leak", "gas rissav", "gas nikal rahi hai", "gas smell", "gandh", "sar dard",
        "hawa me gas", "gas chadh gayi", "dam ghut raha", "co gas", "bf gas", "bfg",
        "cog", "coke oven gas", "bleeder valve", "water seal blown", "flange leak",
        "gasholder", "gas cylinder", "hissing sound", "tezz aawaz", "gas alarm",
        "हवा में गैस", "गैस रिसाव", "दम घुट रहा", "बेहोश"
    ],
    # Fire terms
    "fire": [
        "aag", "fire", "flames", "smoke", "dhuaan", "chatt", "chingari", "sparking",
        "burning smell", "jalne ki badbu", "cable tray fire", "cable basement",
        "transformer blast", "oil fire", "conveyor aag", "pulpit me aag", "shola",
        "आग", "धुआं", "चिंगारी", "लपटें"
    ],
    # Electrical terms
    "electrical_hazard": [
        "current", "shock", "bijli", "jhatka", "breaker", "trip", "panel", "busbar",
        "arc flash", "live wire", "nangi taar", "flashover", "short circuit", "substation",
        "mcc panel", "transformer", "feeder", "loto", "lockout", "step potential",
        "करंट", "झटका", "बिजली", "नंगी तार"
    ],
    # Molten metal terms
    "molten_metal_spill": [
        "hot metal", "liquid steel", "pighla loha", "slag", "splash", "breakout",
        "torpedo", "ladle", "tundish", "runner", "taphole", "mud gun", "splatter",
        "steam explosion", "dhaka", "lal garam loha", "blast furnace runner",
        "पिघला लोहा", "स्लैग", "तपाहोल", "टॉरपीडो"
    ],
    # Chemical terms
    "chemical_spill": [
        "acid", "tezaab", "acid leak", "chemical rissav", "sulfuric", "hydrochloric",
        "caustic soda", "drum puncture", "chlorine", "peeli gas", "ammonia", "fumes",
        "acid jal gaya", "eyewash", "safety shower", "bund wall", "tezaab gira",
        "तेजाब", "एसिड", "केमिकल रिसाव", "आंखों में जलन"
    ],
    # Mechanical terms
    "mechanical_failure": [
        "belt snap", "conveyor jam", "crusher phat gaya", "pulley टूट गई", "gearbox sound",
        "bearing toot gaya", "shaft cut gaya", "jam ho gaya", "fas gaya", "e-stop",
        "pull cord", "vibration", "awaz aa rahi hai", "motor phuk gaya",
        "बेल्ट टूट गई", "जाम हो गया", "मशीन में फंसा"
    ],
    # Confined space terms
    "confined_space_emergency": [
        "manhole", "tank ke andar", "vessel ke andar", "pit me gir gaya", "gutter",
        "naale me", "sewer", "andar fas gaye", "jawab nahi de raha", "behosh andar",
        "oxygen nahi hai", "dam ghut gaya", "scba", "tripod", "air blower",
        "टैंक के अंदर", "गड्ढे में", "मैनहोल", "अंदर बेहोश"
    ],
    # Crane terms
    "crane_lifting_failure": [
        "crane wire cut gaya", "rassi toot gayi", "wire rope split", "hook slip",
        "ladle gir gaya", "load latka hua hai", "crane takra gaya", "brake fail",
        "sling phat gaya", "crane driver fas gaya", "dsl line", "magnet load drop",
        "क्रेन का तार टूटा", "हुक से फिसला", "भार लटक रहा"
    ],
    # Vehicle terms
    "vehicle_traffic_incident": [
        "dumper takkar", "gadi lad gayi", "forklift palat gaya", "loco takra gaya",
        "rail crossing", "patli par", "driver fas gaya", "pahiya chadh gaya",
        "break fail gadi", "diesel rissav", "road block",
        "डंपर पलट गया", "टक्कर हो गई", "ड्राइवर फंसा"
    ],
    # Slip / Fall terms
    "slip_fall": [
        "gir gaya", "slip ho gaya", "machan se gira", "scaffold se gir gaya",
        "sidhi se gira", "fissal gaya", "tel me fisla", "chot lag gayi",
        "kamar toot gayi", "sir phut gaya", "hath pair toot gaya", "harness nahi pehna",
        "ऊंचाई से गिरा", "फिसल गया", "मचान से गिरा", "हड्डी टूट गई"
    ]
}

def expand_vernacular_query(query: str, hazard_type: str | None = None) -> str:
    """
    Expands vernacular search query with domain-specific industrial terminology.
    """
    expanded_parts = [query]
    q_low = query.lower()

    target_categories = [hazard_type] if (hazard_type and hazard_type in DOMAIN_GLOSSARY) else list(DOMAIN_GLOSSARY.keys())

    for cat in target_categories:
        terms = DOMAIN_GLOSSARY[cat]
        # Check if query matches any vernacular slang or technical term
        if any(term in q_low for term in terms):
            # Inject top standard safety anchors from this category
            expanded_parts.extend(terms[:8])
            break

    return " ".join(expanded_parts)
