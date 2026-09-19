"""
Placeholder entity extraction — regex/keyword-based for people-count and
symptoms, standing in for the spaCy NER / BERT token-classification
component in the design doc until there's labeled data to train one.

Zone matching got a semantic upgrade for the same reason classifier.py did:
exact substring matching against zone names only catches a report that uses
the zone's literal name. "Near the gas storage area" describes the Gas
Holder Station without ever saying "Gas Holder Station" — substring
matching misses it, embedding similarity against each zone's name+notes
catches it. Falls back to embeddings only when substring matching finds
nothing, so the cheap exact-match path still wins when it applies.
"""

import json
import re

from app.config import ZONES_PATH
from app.services import embeddings

with open(ZONES_PATH) as f:
    _ZONES = json.load(f)["zones"]

_ZONE_NAME_LOOKUP = {z["name"].lower(): z["zone_id"] for z in _ZONES}
# Deliberately not indexing zone_id (e.g. "SM", "BF1", "GHS") for substring
# matching — short internal codes collide with ordinary English substrings
# ("SM" matched inside "smoke" in testing). Zone IDs aren't something a
# worker would say aloud anyway; only the human-readable name is a
# meaningful signal here.

_ZONE_IDS = [z["zone_id"] for z in _ZONES]
_ZONE_PROFILE_TEXTS = [f"{z['name']}. {z.get('notes', '')}" for z in _ZONES]
_zone_profile_embeddings = None

_ZONE_MATCH_THRESHOLD = 0.35

_SYMPTOM_KEYWORDS = [
    "dizziness", "dizzy", "headache", "nausea", "breathing difficulty",
    "chest tightness", "burns", "burning sensation", "irritation",
    "unconscious", "coughing", "vomiting",
]

_WORD_NUMBERS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "a": 1, "an": 1, "couple of": 2, "few": 3,
}
_NUMBER_TOKEN = r"(\d+|" + "|".join(sorted(_WORD_NUMBERS, key=len, reverse=True)) + r")"
_PEOPLE_COUNT_RE = re.compile(
    rf"\b{_NUMBER_TOKEN}\s*(people|workers|persons|men|colleagues)\b", re.IGNORECASE
)


def _get_zone_profile_embeddings():
    global _zone_profile_embeddings
    if _zone_profile_embeddings is None:
        _zone_profile_embeddings = embeddings.encode(_ZONE_PROFILE_TEXTS)
    return _zone_profile_embeddings


def _semantic_zone_match(text: str) -> str | None:
    profile_vecs = _get_zone_profile_embeddings()
    text_vec = embeddings.encode([text])[0]
    similarities = profile_vecs @ text_vec

    best_idx = int(similarities.argmax())
    if float(similarities[best_idx]) < _ZONE_MATCH_THRESHOLD:
        return None
    return _ZONE_IDS[best_idx]


def extract(text: str, stated_zone_id: str | None = None) -> dict:
    lowered = text.lower()

    mentioned_zone = stated_zone_id
    zone_match_method = "stated" if stated_zone_id else None

    if not mentioned_zone:
        for name, zone_id in _ZONE_NAME_LOOKUP.items():
            if name in lowered:
                mentioned_zone = zone_id
                zone_match_method = "exact"
                break

    if not mentioned_zone:
        semantic_match = _semantic_zone_match(text)
        if semantic_match:
            mentioned_zone = semantic_match
            zone_match_method = "semantic"

    people_match = _PEOPLE_COUNT_RE.search(text)
    people_affected = None
    if people_match:
        token = people_match.group(1).lower()
        people_affected = int(token) if token.isdigit() else _WORD_NUMBERS.get(token)

    symptoms = [s for s in _SYMPTOM_KEYWORDS if s in lowered]

    return {
        "mentioned_zone": mentioned_zone,
        "zone_match_method": zone_match_method,
        "people_affected": people_affected,
        "symptoms": symptoms,
    }


if __name__ == "__main__":
    test_cases = [
        ("Near the gas storage area, I think there's a leak", "GHS"),
        ("Someone got hurt near the cold rolling area where they handle the acids", "CRM"),
        ("There's smoke coming from the big furnace where they make the steel", "SMS"),
    ]
    for text, expected in test_cases:
        result = extract(text)
        status = "OK" if result["mentioned_zone"] == expected else "MISMATCH"
        print(f"[{status}] text={text!r}\n  expected={expected} got={result['mentioned_zone']} (via {result['zone_match_method']})\n")
