from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.tenancy import get_current_user, CurrentUser
from app.services import risk_service

router = APIRouter(prefix="/api/v1/risks", tags=["risks"])


@router.get("")
def get_risks(db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    """GET /api/v1/orgs/{org_id}/risks — US-2.1: Get Execution Risk Summary.
    Computed live (not just read from stale persisted rows) so the feed always
    reflects current state; call POST /refresh to also persist a snapshot."""
    return risk_service.rank_risks(db, current_user.tenant_id)


@router.post("/refresh")
def refresh_risks(db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    findings = risk_service.rank_risks(db, current_user.tenant_id)
    events = risk_service.persist_risk_findings(db, current_user.tenant_id, findings)
    return {"persisted_count": len(events)}
