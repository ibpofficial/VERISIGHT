from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.app.core.database import engine, Base, SessionLocal
from backend.app.core.security import get_password_hash
from backend.app.models import User, UserRole


def init_db(db: Session = None) -> None:
    """Initializes tables and seeds baseline development / evaluation users."""
    Base.metadata.create_all(bind=engine)

    # Lightweight SQLite auto-migration for newly added columns
    try:
        with engine.connect() as conn:
            existing_cols = [row[1] for row in conn.execute(text("PRAGMA table_info(screenings)")).fetchall()]
            if existing_cols:
                if "stage_details" not in existing_cols:
                    conn.execute(text("ALTER TABLE screenings ADD COLUMN stage_details JSON DEFAULT '{}'"))
                if "current_stage" not in existing_cols:
                    conn.execute(text("ALTER TABLE screenings ADD COLUMN current_stage VARCHAR(64)"))
                if "rescan_instructions" not in existing_cols:
                    conn.execute(text("ALTER TABLE screenings ADD COLUMN rescan_instructions TEXT"))
                if "is_aborted" not in existing_cols:
                    conn.execute(text("ALTER TABLE screenings ADD COLUMN is_aborted BOOLEAN DEFAULT 0"))
                conn.commit()
    except Exception:
        pass

    close_session = False
    if db is None:
        db = SessionLocal()
        close_session = True

    try:
        # Check if users table already populated
        existing_user = db.query(User).first()
        if not existing_user:
            default_users = [
                {
                    "email": "officer@verisight.gov.in",
                    "password_hash": get_password_hash("Officer@12345"),
                    "full_name": "Inspector Rajesh Kumar",
                    "role": UserRole.SCREENING_OFFICER,
                    "badge_number": "SSB-2026-8812",
                    "is_active": True
                },
                {
                    "email": "reviewer@verisight.gov.in",
                    "password_hash": get_password_hash("Reviewer@12345"),
                    "full_name": "Reviewer Amit Sharma",
                    "role": UserRole.SENIOR_REVIEWER,
                    "badge_number": "SSB-2026-1045",
                    "is_active": True
                },
                {
                    "email": "senior@verisight.gov.in",
                    "password_hash": get_password_hash("Senior@12345"),
                    "full_name": "Senior Reviewer Priya Nair",
                    "role": UserRole.SENIOR_REVIEWER,
                    "badge_number": "SSB-2026-1044",
                    "is_active": True
                },
                {
                    "email": "admin@verisight.gov.in",
                    "password_hash": get_password_hash("Admin@12345"),
                    "full_name": "System Administrator Verma",
                    "role": UserRole.ADMINISTRATOR,
                    "badge_number": "MHA-HQ-001",
                    "is_active": True
                },
                {
                    "email": "auditor@verisight.gov.in",
                    "password_hash": get_password_hash("Auditor@12345"),
                    "full_name": "Senior Auditor Ananya Sen",
                    "role": UserRole.AUDITOR,
                    "badge_number": "CFSL-DOC-409",
                    "is_active": True
                }
            ]
            for u_data in default_users:
                user = User(**u_data)
                db.add(user)
            db.commit()
    finally:
        if close_session:
            db.close()


if __name__ == "__main__":
    init_db()
    print("Database schema created and initial users seeded successfully.")
