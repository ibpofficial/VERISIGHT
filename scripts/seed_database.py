import os
import sys

# Ensure backend can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import SessionLocal, engine, Base
from backend.app.core.security import get_password_hash
from backend.app.models import User, UserRole
import backend.app.models


DEMO_USERS = [
    {
        "email": "admin@verisight.gov.in",
        "full_name": "Chief Admin Rajesh Verma",
        "role": UserRole.ADMINISTRATOR,
        "password": os.getenv("ADMIN_PASSWORD", "Admin@12345"),
        "badge_number": "ADM-001"
    },
    {
        "email": "officer@verisight.gov.in",
        "full_name": "Screening Officer Ananya Sen",
        "role": UserRole.SCREENING_OFFICER,
        "password": os.getenv("OFFICER_PASSWORD", "Officer@12345"),
        "badge_number": "SCR-104"
    },
    {
        "email": "reviewer@verisight.gov.in",
        "full_name": "Senior Reviewer Vikram Malhotra",
        "role": UserRole.SENIOR_REVIEWER,
        "password": os.getenv("REVIEWER_PASSWORD", "Reviewer@12345"),
        "badge_number": "REV-052"
    },
    {
        "email": "auditor@verisight.gov.in",
        "full_name": "Compliance Auditor Meera Nair",
        "role": UserRole.AUDITOR,
        "password": os.getenv("AUDITOR_PASSWORD", "Auditor@12345"),
        "badge_number": "AUD-019"
    }
]


def seed_users():
    print("Initializing database tables...")
    Base.metadata.create_all(bind=engine)

    print("Seeding demo officers and users...")
    db = SessionLocal()
    try:
        for u in DEMO_USERS:
            existing = db.query(User).filter(User.email == u["email"].lower()).first()
            if not existing:
                new_user = User(
                    email=u["email"].lower(),
                    password_hash=get_password_hash(u["password"]),
                    full_name=u["full_name"],
                    role=u["role"],
                    badge_number=u["badge_number"],
                    is_active=True
                )
                db.add(new_user)
                print(f" -> Created user: {u['email']} [{u['role'].value}]")
            else:
                existing.password_hash = get_password_hash(u["password"])
                print(f" -> Updated credentials for user: {u['email']}")

        db.commit()
        print("Database seeding completed successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_users()
