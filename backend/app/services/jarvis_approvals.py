"""
LeadVoix Business JARVIS — Autonomous Approval & Authorization Gateway
Phase B Safeguard

Responsibilities:
- Human-in-the-loop gates for high-risk autonomous operations.
- Cryptographically signed HMAC-SHA256 tokens.
- Time-bounded validity (configurable TTL, default 24h).
- Strict replay protection: tokens cannot be reused once resolved.
"""

from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import logging
import secrets
from typing import Any, Dict, Optional, Tuple

from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.models.jarvis import JarvisApprovalRecord


logger = logging.getLogger("leadvoix.jarvis.approvals")

DEFAULT_APPROVAL_TTL_HOURS = 24


def _compute_token_hash(raw_token: str) -> str:
    """Computes a secure SHA-256 digest of the raw approval token."""
    secret = (settings.SECRET_KEY or "fallback-secret-for-testing").encode("utf-8")
    return hmac.new(secret, raw_token.encode("utf-8"), hashlib.sha256).hexdigest()


class JarvisApprovalManager:
    """
    Manages generation, validation, expiration, and replay protection for Founder approvals.
    """

    @staticmethod
    def create_request(
        db: Session,
        action_type: str,
        payload_preview: Dict[str, Any],
        task_id: Optional[int] = None,
        risk_tier: str = "high",
        ttl_hours: int = DEFAULT_APPROVAL_TTL_HOURS,
        requested_by: str = "jarvis_autonomous_engine",
    ) -> Tuple[JarvisApprovalRecord, str]:
        """
        Creates an approval record and generates a cryptographically random, signed token.
        Returns:
            (record, raw_token)
        """
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=ttl_hours)
        raw_token = secrets.token_urlsafe(32)
        token_hash = _compute_token_hash(raw_token)

        record = JarvisApprovalRecord(
            task_id=task_id,
            action_type=action_type,
            risk_tier=risk_tier,
            status="pending",
            token_hash=token_hash,
            payload_preview=payload_preview,
            requested_by=requested_by,
            requested_at=now,
            expires_at=expires_at,
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        logger.info(
            "Created %s approval request #%s for action '%s' (expires in %sh)",
            risk_tier.upper(),
            record.id,
            action_type,
            ttl_hours,
        )
        return record, raw_token

    @staticmethod
    def resolve_request(
        db: Session,
        record_id: str,
        token: str,
        decision: str,  # "approved" or "rejected"
        responded_by: str,
    ) -> Dict[str, Any]:
        """
        Validates token signature, expiration, and replay protection before resolving.
        """
        decision_clean = decision.strip().lower()
        if decision_clean not in ("approved", "rejected"):
            return {
                "success": False,
                "reason": "invalid_decision",
                "message": "Decision must be either 'approved' or 'rejected'.",
            }

        now = datetime.now(timezone.utc)
        record = db.query(JarvisApprovalRecord).filter(JarvisApprovalRecord.id == record_id).first()
        if not record:
            return {
                "success": False,
                "reason": "not_found",
                "message": "Approval record not found.",
            }

        # 1. Replay Protection: must be pending
        if record.status != "pending":
            logger.warning(
                "Replay attempt on approval request #%s (current status: %s)",
                record_id,
                record.status,
            )
            return {
                "success": False,
                "reason": "already_resolved",
                "status": record.status,
                "message": f"This approval request was already resolved ({record.status}) by {record.responded_by}.",
            }

        # 2. Expiration Check
        exp_time = record.expires_at
        if exp_time.tzinfo is None:
            exp_time = exp_time.replace(tzinfo=timezone.utc)

        if now > exp_time:
            record.status = "expired"
            record.responded_at = now
            db.commit()
            logger.warning("Approval request #%s has expired at %s", record_id, exp_time)
            return {
                "success": False,
                "reason": "expired",
                "message": "This approval request has expired and can no longer be processed.",
            }

        # 3. Cryptographic Signature Validation
        candidate_hash = _compute_token_hash(token)
        if not hmac.compare_digest(record.token_hash, candidate_hash):
            logger.warning("Invalid signature token presented for approval #%s", record_id)
            return {
                "success": False,
                "reason": "invalid_signature",
                "message": "Invalid authentication token. Authorization rejected.",
            }

        # 4. Apply Resolution
        record.status = decision_clean
        record.responded_by = responded_by
        record.responded_at = now
        db.commit()
        db.refresh(record)

        logger.info(
            "Approval request #%s successfully %s by '%s'",
            record.id,
            decision_clean.upper(),
            responded_by,
        )

        return {
            "success": True,
            "record_id": record.id,
            "status": record.status,
            "action_type": record.action_type,
            "responded_by": responded_by,
            "responded_at": now.isoformat(),
        }
