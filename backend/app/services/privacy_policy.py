"""
Privacy Governance & Biometric Prohibition Enforcement for BSL AI Platform.

Explicit Guarantees:
  1. Strict Prohibition of Biometric / Voice-Print Profiling:
     Voice recordings are processed exclusively for ephemeral speech-to-text transcription.
     No acoustic embedding, pitch tracking, speaker identification, or voice-print
     hashing algorithms are included or permitted on the platform.
  2. Frontline Consent Transparency:
     Bilingual notices displayed in Hindi and English prior to voice capture.
  3. Scoped Media Access Control:
     Raw audio and visual evidence endpoints are restricted to authorized safety officers
     and control room personnel.
"""

from __future__ import annotations

import logging
from typing import Any

from app.services.rbac import AuthContext, UserRole

logger = logging.getLogger(__name__)

CONSENT_STATEMENTS = {
    "en": {
        "title": "Industrial Safety Data Privacy & Worker Consent",
        "voice_consent": (
            "Voice recordings are processed solely for automated incident transcription and emergency dispatch. "
            "No biometric voice-print, acoustic speaker profiling, or voice identification is performed. "
            "Voice data is retained strictly in accordance with factory safety compliance policies."
        ),
        "photo_consent": (
            "Photo and video evidence is completely optional and used only to corroborate physical hazard conditions. "
            "Evidence is stored securely on plant servers and accessible only to authorized safety personnel."
        ),
        "retention_notice": "Media is automatically purged after the plant's statutory retention window.",
    },
    "hi": {
        "title": "औद्योगिक सुरक्षा डेटा गोपनीयता एवं कर्मचारी सहमति",
        "voice_consent": (
            "आवाज रिकॉर्डिंग का उपयोग केवल स्वचालित आपातकालीन ट्रांसक्रिप्शन और त्वरित सहायता के लिए किया जाता है। "
            "कोई बायोमेट्रिक वॉयस-प्रिंट या वक्ता पहचान नहीं की जाती है। "
            "डेटा केवल फैक्ट्री सुरक्षा नियमों के तहत सुरक्षित रखा जाता है।"
        ),
        "photo_consent": (
            "फोटो या वीडियो प्रमाण पूरी तरह से वैकल्पिक है और केवल खतरे की स्थिति की पुष्टि के लिए उपयोग किया जाता है। "
            "यह केवल अधिकृत सुरक्षा अधिकारियों के लिए ही उपलब्ध है।"
        ),
        "retention_notice": "निर्धारित अवधि के बाद मीडिया डेटा स्वतः हटा दिया जाता है।",
    },
}


def assert_no_biometric_collection() -> bool:
    """
    Architectural assertion verifying that no biometric feature extractor is active.
    Can be called during startup and audit checks.
    """
    # Verify no biometric libraries or models are loaded
    forbidden_modules = ["speechbrain.inference.speaker", "resemble_enhance", "pyannote.audio"]
    import sys
    for mod in forbidden_modules:
        if mod in sys.modules:
            raise RuntimeError(f"Biometric violation: Forbidden speaker identification module '{mod}' detected!")
    return True


def check_media_access(auth: AuthContext, ticket_plant_id: str, ticket_worker_id: str | None = None) -> bool:
    """
    Verifies that the accessing user is authorized to inspect raw audio or photographic evidence.
    Authorized: Safety Officers, Control Room, Admins, or the reporting worker.
    """
    if auth.role in (UserRole.ADMIN, UserRole.SAFETY_OFFICER, UserRole.CONTROL_ROOM):
        return auth.plant_id == ticket_plant_id

    if auth.role == UserRole.WORKER and ticket_worker_id and auth.user_id == ticket_worker_id:
        return auth.plant_id == ticket_plant_id

    return False
