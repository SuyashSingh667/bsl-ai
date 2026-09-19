import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

VERIFICATION_QUESTIONS_PATH = PROJECT_ROOT / "verification_questions.json"
ZONES_PATH = PROJECT_ROOT / "spatial_impact" / "zones.json"
HAZARD_BANDS_PATH = PROJECT_ROOT / "spatial_impact" / "hazard_bands.json"
RAG_DOCUMENTS_DIR = PROJECT_ROOT / "rag_documents"

DATABASE_URL = f"sqlite:///{BACKEND_DIR / 'data' / 'bsl.db'}"

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

# "small" is the intended live-interaction default per voice_pipeline.md.
# Pinned to "base" here because this session's network kept stalling
# mid-download on the "small" weights (huggingface_hub download reliability
# issue, not a code issue) — "base" was already fully cached from prior
# unrelated use. Swap back to "small"/"medium" once a stable download
# completes; nothing else in the code depends on which size is loaded.
WHISPER_MODEL_SIZE = "small"

AUDIO_UPLOAD_DIR = BACKEND_DIR / "data" / "audio"
PHOTO_UPLOAD_DIR = BACKEND_DIR / "data" / "photos"

# Necessary cases: Categories requiring photographic or video proof as physical evidence
CATEGORIES_REQUIRING_PHOTO = [
    "fire",
    "molten_metal_spill",
    "chemical_spill",
    "gas_leak",
    "crane_lifting_failure",
    "vehicle_traffic_incident",
    "electrical_hazard",
    "mechanical_failure",
    "confined_space_emergency",
]
CATEGORIES_REQUIRING_MEDIA = CATEGORIES_REQUIRING_PHOTO

INCIDENT_CATEGORIES = [
    "gas_leak",
    "fire",
    "electrical_hazard",
    "mechanical_failure",
    "slip_fall",
    "ppe_violation",
    "molten_metal_spill",
    "confined_space_emergency",
    "crane_lifting_failure",
    "vehicle_traffic_incident",
    "chemical_spill",
]

# Baseline severity weight per category, used only until a trained severity
# model replaces it. Reflects the real historical-accident skew documented in
# rag_documents/reference_data/ndma_chemical_disaster_reference.md (gas
# releases and explosions dominate fatality-causing incidents).
CATEGORY_BASELINE_SEVERITY = {
    "gas_leak": 0.8,
    "molten_metal_spill": 0.85,
    "confined_space_emergency": 0.85,
    "fire": 0.7,
    "crane_lifting_failure": 0.65,
    "chemical_spill": 0.6,
    "electrical_hazard": 0.55,
    "vehicle_traffic_incident": 0.5,
    "mechanical_failure": 0.4,
    "slip_fall": 0.2,
    "ppe_violation": 0.15,
}
