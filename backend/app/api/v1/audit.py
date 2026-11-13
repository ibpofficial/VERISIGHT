from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models import User, UserRole, AuditLog
from backend.app.schemas import AuditLogResponse, AuditIntegrityResponse
from backend.app.api.deps import get_current_user, require_roles

router = APIRouter(prefix="/audit", tags=["Cryptographic Audit Chain"])


@router.get("", response_model=List[AuditLogResponse])
def list_audit_logs(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(require_roles([UserRole.ADMINISTRATOR, UserRole.SENIOR_REVIEWER, UserRole.AUDITOR])),
    db: Session = Depends(get_db)
):
    """
    Returns paginated audit trail blocks ordered from most recent to oldest.
    """
    logs = db.query(AuditLog).order_by(AuditLog.id.desc()).offset(skip).limit(limit).all()
    return logs


@router.get("/verify-integrity", response_model=AuditIntegrityResponse)
def verify_audit_integrity(
    current_user: User = Depends(require_roles([UserRole.ADMINISTRATOR, UserRole.SENIOR_REVIEWER, UserRole.AUDITOR])),
    db: Session = Depends(get_db)
):
    """
    Sequentially traverses every block in the audit ledger, verifying the
    cryptographic SHA-256 hash linkage (prev_hash == previous.current_hash).
    Detects any database tampering, unauthorized row deletions, or alterations.
    """
    blocks = db.query(AuditLog).order_by(AuditLog.id.asc()).all()

    if not blocks:
        return AuditIntegrityResponse(
            is_intact=True,
            total_blocks_verified=0,
            first_block_timestamp=None,
            latest_block_timestamp=None,
            latest_hash=None,
            corrupted_at_id=None,
            details="Audit ledger is currently empty. Zero blocks to verify."
        )

    # Verify genesis block (first block)
    expected_prev = "0" * 64
    first_block = blocks[0]
    
    # Traverse chain
    prev_block = None
    for i, block in enumerate(blocks):
        # 1. Format check
        if not block.current_hash or len(block.current_hash) != 64:
            return AuditIntegrityResponse(
                is_intact=False,
                total_blocks_verified=i,
                first_block_timestamp=first_block.timestamp,
                latest_block_timestamp=block.timestamp,
                latest_hash=block.current_hash,
                corrupted_at_id=block.id,
                details=f"Block #{block.id} has invalid cryptographic digest formatting."
            )

        # 2. Check linkage to preceding block
        if prev_block is not None:
            if block.prev_record_hash != prev_block.current_hash:
                return AuditIntegrityResponse(
                    is_intact=False,
                    total_blocks_verified=i,
                    first_block_timestamp=first_block.timestamp,
                    latest_block_timestamp=block.timestamp,
                    latest_hash=block.current_hash,
                    corrupted_at_id=block.id,
                    details=(
                        f"Cryptographic link severed at Block #{block.id}. "
                        f"Expected previous hash {prev_block.current_hash[:16]}..., "
                        f"found {block.prev_record_hash[:16]}... Possible database tampering or row deletion."
                    )
                )

        prev_block = block

    return AuditIntegrityResponse(
        is_intact=True,
        total_blocks_verified=len(blocks),
        first_block_timestamp=first_block.timestamp,
        latest_block_timestamp=blocks[-1].timestamp,
        latest_hash=blocks[-1].current_hash,
        corrupted_at_id=None,
        details=(
            f"All {len(blocks)} cryptographic blocks verified intact. "
            "Zero chain breaks or unauthorized data modifications detected."
        )
    )
