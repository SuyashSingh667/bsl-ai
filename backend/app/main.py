from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import AUDIO_UPLOAD_DIR, PHOTO_UPLOAD_DIR
from app.database import Base, engine
from app.routers import (
    admin,
    analytics,
    guidance,
    incidents,
    integrations,
    similar_incidents,
    tickets,
    transcription,
    translate,
    tts,
    verification,
)
from app.services import rag

AUDIO_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
PHOTO_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    # Ensure columns exist in SQLite database if created prior to schema addition
    with engine.connect() as conn:
        from sqlalchemy import text
        try:
            conn.execute(text("ALTER TABLE tickets ADD COLUMN photo_proof_path VARCHAR;"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE tickets ADD COLUMN requires_photo_proof BOOLEAN DEFAULT 0;"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE tickets ADD COLUMN media_type TEXT;"))
            conn.commit()
        except Exception:
            pass
        for col_def in [
            "plant_id VARCHAR DEFAULT 'bsl_bokaro'",
            "reporting_mode VARCHAR DEFAULT 'personal'",
            "reporter_supervisor_id VARCHAR",
            "worker_badge_id VARCHAR",
            "kiosk_station_id VARCHAR",
            "is_anonymous BOOLEAN DEFAULT 0",
            "shift VARCHAR",
            "anonymous_tracking_code VARCHAR",
            "lifecycle_stage VARCHAR DEFAULT 'received'",
            "corrective_action TEXT",
            "assigned_to VARCHAR",
            "due_date TIMESTAMP",
            "closed_at TIMESTAMP",
            "closure_time_hours FLOAT",
            "closure_evidence_path VARCHAR",
            "closure_notes TEXT",
            "dispatch_status VARCHAR DEFAULT 'pending'",
            "dispatched_at TIMESTAMP",
            "acknowledged_at TIMESTAMP",
            "acknowledged_by VARCHAR",
            "on_site_at TIMESTAMP",
            "on_site_by VARCHAR",
            "ack_deadline TIMESTAMP",
            "escalation_level INTEGER DEFAULT 0",
            "escalated_at TIMESTAMP",
            "escalated_to VARCHAR",
            # Phase 8 operational metrics flags
            "completed_offline BOOLEAN DEFAULT 0",
            "false_alarm BOOLEAN DEFAULT 0",
        ]:
            try:
                conn.execute(text(f"ALTER TABLE tickets ADD COLUMN {col_def};"))
                conn.commit()
            except Exception:
                pass
    rag.build_index()
    yield


app = FastAPI(title="BSL AI Safety Intelligence Platform", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(incidents.router)
app.include_router(transcription.router)
app.include_router(translate.router)
app.include_router(tts.router)
app.include_router(verification.router)
app.include_router(guidance.router)
app.include_router(tickets.router)
app.include_router(similar_incidents.router)
app.include_router(admin.router)
app.include_router(integrations.router)
app.include_router(analytics.router)

app.mount("/audio", StaticFiles(directory=str(AUDIO_UPLOAD_DIR)), name="audio")
app.mount("/photos", StaticFiles(directory=str(PHOTO_UPLOAD_DIR)), name="photos")


@app.get("/health")
def health():
    return {"status": "ok"}
