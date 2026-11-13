"""
LeadVoix Business JARVIS — FastAPI Router
Phase 1 MVP — Phase A Hardened

Endpoints:
- GET  /api/jarvis/health        — Health, feature flag status and configuration checks.
- GET  /api/jarvis/summary       — Read-only metrics summary for admin dashboard/review.
- POST /api/jarvis/digest/trigger — Triggers on-demand or scheduled digest dispatch with durable idempotency.

Security:
- Exclusively uses get_jarvis_read_only_db dependency for database access.
- Requires admin privileges for all data access and triggering endpoints.
- Zero write permissions available through JARVIS database session.
"""

from datetime import datetime
import os
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.models.user import User
from backend.app.services.jarvis_audit import (
    evaluate_worker_health,
    get_latest_worker_heartbeat,
)
from backend.app.services.jarvis_collector import (
    calculate_digest_window,
    collect_jarvis_metrics,
    get_internal_org_id,
    get_jarvis_database_url,
    get_jarvis_read_only_db,
    get_jarvis_timezone,
    is_readonly_db_required,
)
from backend.app.services.jarvis_digest import (
    format_executive_digest,
    generate_and_dispatch_digest,
    get_telegram_credentials,
    is_jarvis_enabled,
    mask_token,
)
from backend.app.utils.dependencies import get_current_admin_user


router = APIRouter(
    prefix="/api/jarvis",
    tags=["JARVIS Business Digest"],
)


class JarvisTriggerRequest(BaseModel):
    digest_type: str = Field(default="custom", description="Digest type: 'morning', 'evening', or 'custom'")
    date: Optional[str] = Field(default=None, description="Optional target date in YYYY-MM-DD format")
    force: bool = Field(default=False, description="Set True to bypass idempotency/cooldown guards and force dispatch")
    send_telegram: bool = Field(default=True, description="Whether to dispatch outbound Telegram notification")


@router.get("/health")
def get_jarvis_health(
    db: Optional[Session] = Depends(get_jarvis_read_only_db),
) -> Dict[str, Any]:
    """
    Returns the operational health, configuration state, and 24/7 background worker telemetry.
    Does not require authentication so monitoring agents can poll it.
    Strictly read-only database session used for heartbeat validation.
    """
    enabled = is_jarvis_enabled()
    creds = get_telegram_credentials()
    has_custom_db = bool(os.getenv("JARVIS_DATABASE_URL"))
    readonly_required = is_readonly_db_required()

    try:
        tz = get_jarvis_timezone()
        tz_name = getattr(tz, "key", str(tz))
    except Exception:
        tz_name = "invalid_configuration"

    worker_status = "disabled" if not enabled else "unavailable"
    worker_info: Dict[str, Any] = {
        "status": worker_status,
        "worker_id": None,
        "last_heartbeat": None,
        "details": None,
    }

    session: Optional[Session] = db if isinstance(db, Session) else None
    if session is not None and enabled:
        try:
            hb = get_latest_worker_heartbeat(session, organization_id=get_internal_org_id())
            worker_status, worker_info = evaluate_worker_health(hb)
        except Exception as exc:
            worker_status = "unavailable"
            worker_info = {
                "status": "unavailable",
                "worker_id": None,
                "last_heartbeat": None,
                "details": {"error": type(exc).__name__},
            }

    # Overall system health:
    # If disabled: "disabled"
    # If session provided:
    #   "healthy" ONLY when worker_status == "running"
    #   "degraded" if worker is stale, stopped, or unavailable (never reported as healthy!)
    # If session is None (e.g. lightweight unpolled call):
    #   "healthy" if enabled else "disabled"
    if not enabled:
        overall_status = "disabled"
    elif session is not None:
        overall_status = "healthy" if worker_status == "running" else "degraded"
    else:
        overall_status = "healthy"

    return {
        "status": overall_status,
        "enabled": enabled,
        "service": "LeadVoix Business JARVIS (Phase 1 MVP — Phase B Hardened)",
        "timezone": tz_name,
        "internal_org_id": get_internal_org_id(),
        "read_only_db_custom": has_custom_db,
        "read_only_enforced": readonly_required,
        "telegram_configured": bool(creds.get("bot_token") and creds.get("chat_id")),
        "worker_status": worker_status,
        "worker_id": worker_info.get("worker_id"),
        "last_heartbeat": worker_info.get("last_heartbeat"),
        "worker": worker_info,
    }


@router.get("/summary")
def get_jarvis_summary(
    digest_type: str = Query(default="custom", pattern="^(morning|evening|custom)$"),
    date: Optional[str] = Query(default=None, description="Optional target date YYYY-MM-DD"),
    db: Session = Depends(get_jarvis_read_only_db),
    current_user: User = Depends(get_current_admin_user),
) -> Dict[str, Any]:
    """
    Returns an aggregated read-only summary for internal admin review without sending Telegram messages.
    Uses strictly read-only database session.
    Requires admin privileges.
    """
    if not is_jarvis_enabled():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="JARVIS is disabled via ENABLE_JARVIS=false",
        )

    parsed_date = None
    if date:
        try:
            parsed_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Expected YYYY-MM-DD.",
            )

    start_utc, end_utc, window_label = calculate_digest_window(digest_type, target_date=parsed_date)
    org_id = get_internal_org_id()

    metrics = collect_jarvis_metrics(db, org_id=org_id, start_utc=start_utc, end_utc=end_utc)
    formatted_digest = format_executive_digest(metrics, digest_type, window_label)

    return {
        "status": "success",
        "digest_type": digest_type,
        "window_label": window_label,
        "metrics": metrics,
        "formatted_digest": formatted_digest,
    }


@router.post("/digest/trigger")
def trigger_jarvis_digest(
    payload: JarvisTriggerRequest,
    db: Session = Depends(get_jarvis_read_only_db),
    current_user: User = Depends(get_current_admin_user),
) -> Dict[str, Any]:
    """
    Manually triggers generation and dispatch of a JARVIS digest.
    Guarded by durable idempotency and retry cooldowns to avoid duplicate transmissions.
    Uses strictly read-only database session.
    Requires admin privileges.
    """
    if not is_jarvis_enabled():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="JARVIS is disabled via ENABLE_JARVIS=false",
        )

    parsed_date = None
    if payload.date:
        try:
            parsed_date = datetime.strptime(payload.date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Expected YYYY-MM-DD.",
            )

    result = generate_and_dispatch_digest(
        digest_type=payload.digest_type,
        target_date=parsed_date,
        force=payload.force,
        send_telegram=payload.send_telegram,
        db=db,
    )

    return result
