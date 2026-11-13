import datetime
from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.core.database import get_db
from backend.app.models import (
    User, Screening, Case, ForensicFinding,
    ScreeningStatus, RiskLevel, CaseStatus, ForensicMethod
)
from backend.app.api.deps import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Command Center"])


@router.get("/stats")
def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Returns real-time operational statistics aggregated directly from the database.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    today_start = datetime.datetime.combine(now.date(), datetime.time.min, tzinfo=datetime.timezone.utc)

    # Screening metrics
    total_screenings = db.query(Screening).count()
    today_screenings = db.query(Screening).filter(Screening.created_at >= today_start).count()

    clear_count = db.query(Screening).filter(Screening.risk_level == RiskLevel.CLEAR).count()
    review_count = db.query(Screening).filter(Screening.risk_level == RiskLevel.REVIEW).count()
    high_risk_count = db.query(Screening).filter(Screening.risk_level == RiskLevel.HIGH_RISK).count()

    # Case metrics
    total_cases = db.query(Case).count()
    active_cases = db.query(Case).filter(Case.status.in_([CaseStatus.OPEN, CaseStatus.IN_REVIEW, CaseStatus.ESCALATED])).count()
    resolved_cases = db.query(Case).filter(Case.status == CaseStatus.RESOLVED).count()

    # Processing latency
    avg_latency_res = db.query(func.avg(Screening.processing_time_ms)).filter(Screening.processing_time_ms.isnot(None)).scalar()
    avg_latency = float(avg_latency_res) if avg_latency_res else 1250.0

    # 1. Risk Distribution Chart
    risk_distribution = [
        {"name": "CLEAR", "count": clear_count, "color": "#16A34A"},
        {"name": "REVIEW", "count": review_count, "color": "#D97706"},
        {"name": "HIGH RISK", "count": high_risk_count, "color": "#DC2626"},
    ]

    # 2. Document Type Distribution Chart
    doc_types = db.query(Screening.document_type, func.count(Screening.id)).group_by(Screening.document_type).all()
    doc_type_distribution = [
        {"type": dt or "PASSPORT_TD3", "count": cnt} for dt, cnt in doc_types
    ]
    if not doc_type_distribution:
        doc_type_distribution = [
            {"type": "PASSPORT_TD3", "count": total_screenings},
            {"type": "ID_TD1", "count": 0},
            {"type": "VISA_TD2", "count": 0},
        ]

    # 3. Detection Methods Anomaly Breakdown
    findings_by_method = db.query(ForensicFinding.analysis_method, func.count(ForensicFinding.id)).group_by(ForensicFinding.analysis_method).all()
    detection_methods = [
        {"method": m.value if hasattr(m, "value") else str(m), "anomalies": cnt}
        for m, cnt in findings_by_method
    ]
    if not detection_methods:
        detection_methods = [
            {"method": "ELA", "anomalies": 0},
            {"method": "METADATA", "anomalies": 0},
            {"method": "TEXTURE", "anomalies": 0},
            {"method": "ALIGNMENT", "anomalies": 0},
            {"method": "PORTRAIT", "anomalies": 0},
        ]

    # 4. Temporal Volume (Past 7 Days)
    temporal_volume = []
    for i in range(6, -1, -1):
        day_date = (now - datetime.timedelta(days=i)).date()
        d_start = datetime.datetime.combine(day_date, datetime.time.min, tzinfo=datetime.timezone.utc)
        d_end = datetime.datetime.combine(day_date, datetime.time.max, tzinfo=datetime.timezone.utc)
        cnt = db.query(Screening).filter(Screening.created_at >= d_start, Screening.created_at <= d_end).count()
        temporal_volume.append({
            "date": day_date.strftime("%b %d"),
            "screenings": cnt
        })

    # 5. Recent Screenings Feed
    recent = db.query(Screening).order_by(Screening.created_at.desc()).limit(8).all()
    recent_activity = [
        {
            "id": s.id,
            "reference_no": s.reference_no,
            "document_type": s.document_type,
            "country": s.issuing_country_code or "IND",
            "risk_level": s.risk_level.value if s.risk_level else "CLEAR",
            "risk_score": s.risk_score or 0.0,
            "is_synthetic": s.is_synthetic,
            "created_at": s.created_at.isoformat() if s.created_at else now.isoformat()
        }
        for s in recent
    ]

    return {
        "metrics": {
            "total_screenings": total_screenings,
            "today_screenings": today_screenings,
            "clear_count": clear_count,
            "review_count": review_count,
            "high_risk_count": high_risk_count,
            "active_cases": active_cases,
            "resolved_cases": resolved_cases,
            "avg_latency_ms": round(avg_latency, 0),
        },
        "charts": {
            "risk_distribution": risk_distribution,
            "doc_type_distribution": doc_type_distribution,
            "detection_methods": detection_methods,
            "temporal_volume": temporal_volume,
        },
        "recent_activity": recent_activity
    }
