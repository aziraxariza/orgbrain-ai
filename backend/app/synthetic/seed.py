"""Runs on container startup (see docker-compose command). Idempotent: skips if
any organization already exists, so restarts don't duplicate demo data."""
from app.database import SessionLocal
from app.models.organization import Organization
from app.synthetic.generator import generate_organization


def main():
    db = SessionLocal()
    try:
        if db.query(Organization).first() is not None:
            print("[seed] organization already exists, skipping synthetic data generation")
            return
        print("[seed] generating synthetic organization...")
        org = generate_organization(db)
        print(f"[seed] done. org_id={org.organization_id} login=admin@acmedemo.com / password123")
    finally:
        db.close()


if __name__ == "__main__":
    main()
