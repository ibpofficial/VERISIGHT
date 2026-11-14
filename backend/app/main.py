import os
import uuid
import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.app.core.config import settings
from backend.app.core.database import engine, Base, get_db
import backend.app.models  # Ensure all models are registered with Base.metadata
from backend.app.api.v1 import auth, screenings, forensics, risk, cases, reports, audit, dashboard, admin, face, quick_check


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure local storage directories exist
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.PROCESSED_DIR, exist_ok=True)
    os.makedirs(settings.REPORTS_DIR, exist_ok=True)

    # Initialize tables and seed baseline users
    from backend.app.core.init_db import init_db
    init_db()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="VERISIGHT — AI-Based Fake Identity & Document Screening System (SIH 2026, PS 26188)",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(screenings.router, prefix=settings.API_V1_STR)
app.include_router(forensics.router, prefix=settings.API_V1_STR)
app.include_router(risk.router, prefix=settings.API_V1_STR)
app.include_router(cases.router, prefix=settings.API_V1_STR)
app.include_router(reports.router, prefix=settings.API_V1_STR)
app.include_router(audit.router, prefix=settings.API_V1_STR)
app.include_router(dashboard.router, prefix=settings.API_V1_STR)
app.include_router(admin.router, prefix=settings.API_V1_STR)
app.include_router(face.router, prefix=settings.API_V1_STR)
app.include_router(quick_check.router, prefix=settings.API_V1_STR)


@app.get("/health/live", tags=["Health"])
def health_live():
    """Liveness probe: verifies the service process is active and accepting connections."""
    return {
        "status": "ALIVE",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }


@app.get("/health/ready", tags=["Health"])
def health_ready(response: Response, db: Session = Depends(get_db)):
    """
    Readiness probe: performs genuine checks on database connection,
    storage filesystem writability, and OCR engine availability.
    """
    # 1. Database Connectivity Probe
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_status = "CONNECTED"
        db_ok = True
    except Exception as e:
        db_status = f"ERROR: {str(e)}"

    # 2. Upload Storage Writability Probe
    storage_ok = False
    try:
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        canary = os.path.join(settings.UPLOAD_DIR, f".probe_{uuid.uuid4().hex[:8]}")
        with open(canary, "w") as f:
            f.write("health_ok")
        os.remove(canary)
        storage_status = "WRITABLE"
        storage_ok = True
    except Exception as e:
        storage_status = f"ERROR: {str(e)}"

    # 3. OCR Engine Probes
    ocr_status = {}
    try:
        import pytesseract
        t_ver = pytesseract.get_tesseract_version()
        ocr_status["tesseract"] = f"AVAILABLE (v{t_ver})"
    except Exception as e:
        ocr_status["tesseract"] = f"UNAVAILABLE: {str(e)}"

    try:
        import paddleocr
        ocr_status["paddleocr"] = "AVAILABLE"
    except Exception:
        ocr_status["paddleocr"] = "NOT_INSTALLED"

    is_ready = db_ok and storage_ok
    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "READY" if is_ready else "NOT_READY",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database": db_status,
        "storage": storage_status,
        "ocr_engines": ocr_status,
        "worker": "OPERATIONAL",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }


@app.get("/health", tags=["Health"])
def health_check(response: Response, db: Session = Depends(get_db)):
    """Backwards-compatible health endpoint calling readiness probe."""
    res = health_ready(response, db)
    if res["status"] == "READY":
        res["status"] = "HEALTHY"
    return res


@app.get("/", tags=["Root"])
def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "mission": "Smart India Hackathon 2026 PS 26188: Explainable Identity & Document Screening",
        "docs_url": f"{settings.API_V1_STR}/docs",
        "status": "OPERATIONAL"
    }
