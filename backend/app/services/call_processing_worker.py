import json
import logging
import re
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Callable, Optional

from sqlalchemy import and_, or_, func, text, update
from sqlalchemy.orm import Session

from backend.app.db.database import SessionLocal
from backend.app.models.activity import Activity
from backend.app.models.agent import Agent
from backend.app.models.agent_call import AgentCall
from backend.app.models.agent_call_intelligence import AgentCallIntelligence
from backend.app.models.agent_call_summary import AgentCallSummary
from backend.app.models.call_processing_job import CallProcessingJob
from backend.app.models.contact import Contact
from backend.app.models.deal import Deal
from backend.app.models.lead import Lead
from backend.app.models.task import Task
from backend.app.models.user import User
from backend.app.services.agent_call_analysis import (
    analyze_call_transcript,
    build_transcript_text,
)
from backend.app.services.agent_call_intelligence import (
    analyze_call_intelligence,
)
from backend.app.services.pipeline_automation import (
    automate_pipeline_and_deal,
)
from backend.app.utils.phone import normalize_phone

logger = logging.getLogger(__name__)


class WorkerOutcome(str, Enum):
    SUCCESS = "success"
    ALREADY_PROCESSED = "already_processed"
    EMPTY_TRANSCRIPT = "empty_transcript"
    NOT_ELIGIBLE = "not_eligible"
    RETRYABLE_FAILURE = "retryable_failure"
    PERMANENT_FAILURE = "permanent_failure"
    FENCE_LOST = "fence_lost"
    NO_JOB_AVAILABLE = "no_job_available"


@dataclass
class ClaimedJob:
    job_id: int
    agent_call_id: int
    job_type: str
    claim_token: str
    attempts: int
    max_attempts: int
    locked_by: str


def get_dialect_name(db: Session) -> str:
    """Returns the dialect name ('postgresql', 'sqlite', etc.)."""
    try:
        bind = db.get_bind() if hasattr(db, "get_bind") else getattr(db, "bind", None)
        if bind and hasattr(bind, "dialect") and hasattr(bind.dialect, "name"):
            return bind.dialect.name
    except Exception:
        pass
    return "postgresql"


def get_db_now(dialect_name: str):
    """Returns database NOW() expression for PostgreSQL, or UTC datetime for SQLite."""
    if dialect_name == "postgresql":
        return func.now()
    return datetime.now(timezone.utc)


def get_db_future_time(dialect_name: str, seconds: int):
    """Returns safely parameterized future timestamp expression for PostgreSQL or SQLite."""
    if dialect_name == "postgresql":
        return func.now() + text("make_interval(secs => :secs)").bindparams(secs=float(seconds))
    return datetime.now(timezone.utc) + timedelta(seconds=seconds)


_ALERTED_DEAD_LETTER_JOB_IDS: set[int] = set()
DEAD_LETTER_ALERT_TAG = "[DEAD_LETTER_ALERTED]"

_SENSITIVE_KEY_REGEX = re.compile(r"sk-[a-zA-Z0-9_\-]{16,}", re.IGNORECASE)
_BEARER_REGEX = re.compile(r"bearer\s+[a-zA-Z0-9_\-\.]{16,}", re.IGNORECASE)
_SECRET_PAIR_REGEX = re.compile(
    r"(?i)\b(token|key|secret|password|auth_token)\b\s*[=:]\s*['\"]?[a-zA-Z0-9_\-]{8,}['\"]?"
)
_EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
_PHONE_REGEX = re.compile(r"\+?[1-9]\d{9,14}")


def classify_safe_error_category(raw_error: Optional[str]) -> str:
    """Categorizes raw error strings into a coarse, safe error category without sensitive data."""
    if not raw_error:
        return "UNKNOWN_ERROR"
    err_lower = raw_error.lower()
    if "lease expired" in err_lower or "lease" in err_lower:
        return "LEASE_EXPIRED"
    if any(k in err_lower for k in ("api key", "401", "authentication", "unauthorized")):
        return "OPENAI_AUTH_ERROR"
    if any(k in err_lower for k in ("rate limit", "429", "quota")):
        return "RATE_LIMIT"
    if any(k in err_lower for k in ("operationalerror", "integrityerror", "database", "deadlock")):
        return "DATABASE_ERROR"
    if any(k in err_lower for k in ("timeout", "timed out", "econnreset", "connection")):
        return "NETWORK_TIMEOUT"
    if any(k in err_lower for k in ("validation error", "valueerror", "typeerror", "schema")):
        return "SCHEMA_VALIDATION_ERROR"
    return "UNEXPECTED_ERROR"


def sanitize_error_summary(raw_error: Optional[str], max_length: int = 150) -> str:
    """Redacts credentials, tokens, emails, phone numbers, and secrets from error text."""
    if not raw_error:
        return "No error details available"
    cleaned = raw_error.strip()
    if DEAD_LETTER_ALERT_TAG in cleaned:
        cleaned = cleaned.replace(DEAD_LETTER_ALERT_TAG, "").strip()
    cleaned = _SENSITIVE_KEY_REGEX.sub("[REDACTED_API_KEY]", cleaned)
    cleaned = _BEARER_REGEX.sub("Bearer [REDACTED_TOKEN]", cleaned)
    cleaned = _SECRET_PAIR_REGEX.sub(r"\1=[REDACTED]", cleaned)
    cleaned = _EMAIL_REGEX.sub("[REDACTED_EMAIL]", cleaned)
    cleaned = _PHONE_REGEX.sub("[REDACTED_PHONE]", cleaned)
    cleaned = " ".join(cleaned.split())
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length].rstrip() + "..."
    return cleaned


def report_dead_letter_transition(
    db: Session,
    job_id: int,
    agent_call_id: int,
    attempts: int,
    max_attempts: int,
    raw_error: Optional[str],
) -> bool:
    """
    Safely reports a job transition to dead_letter with structured logging.
    Guarantees duplicate alert suppression via:
      1. In-memory job_id tracking set (_ALERTED_DEAD_LETTER_JOB_IDS).
      2. Check for DEAD_LETTER_ALERT_TAG in raw_error.
    Resolves organization_id from AgentCall.
    Returns True if an alert was emitted, False if suppressed.
    """
    if job_id in _ALERTED_DEAD_LETTER_JOB_IDS:
        return False

    if raw_error and DEAD_LETTER_ALERT_TAG in raw_error:
        _ALERTED_DEAD_LETTER_JOB_IDS.add(job_id)
        return False

    _ALERTED_DEAD_LETTER_JOB_IDS.add(job_id)

    org_id = None
    try:
        call = db.query(AgentCall).filter(AgentCall.id == agent_call_id).first()
        if call:
            org_id = call.organization_id
    except Exception as exc:
        logger.warning("Could not resolve organization_id for job %s: %s", job_id, exc)

    category = classify_safe_error_category(raw_error)
    sanitized_error = sanitize_error_summary(raw_error)

    logger.error(
        "[DEAD_LETTER_ALERT] job_id=%s organization_id=%s attempts=%s max_attempts=%s category=%s error=%s",
        job_id,
        org_id,
        attempts,
        max_attempts,
        category,
        sanitized_error,
        extra={
            "event": "dead_letter_transition",
            "job_id": job_id,
            "organization_id": org_id,
            "attempts": attempts,
            "max_attempts": max_attempts,
            "category": category,
            "sanitized_error": sanitized_error,
        },
    )
    return True


def reap_stale_dead_letter_jobs(
    db: Session,
    job_type: str = "call_intelligence",
) -> int:
    """
    Finds processing jobs with expired leases whose attempts have reached or exceeded
    max_attempts, and atomically transitions them to 'dead_letter'.
    Preserves claim-token and state safety, and emits structured dead-letter alerts with suppression.
    """
    dialect = get_dialect_name(db)
    now_expr = get_db_now(dialect)

    stale_jobs = (
        db.query(
            CallProcessingJob.id,
            CallProcessingJob.agent_call_id,
            CallProcessingJob.attempts,
            CallProcessingJob.max_attempts,
            CallProcessingJob.last_error,
        )
        .filter(
            CallProcessingJob.job_type == job_type,
            CallProcessingJob.status == "processing",
            CallProcessingJob.attempts >= CallProcessingJob.max_attempts,
            CallProcessingJob.lease_expires_at < now_expr,
        )
        .all()
    )

    reap_error = f"{DEAD_LETTER_ALERT_TAG} Lease expired after reaching maximum attempts"

    stmt = (
        update(CallProcessingJob)
        .where(
            CallProcessingJob.job_type == job_type,
            CallProcessingJob.status == "processing",
            CallProcessingJob.attempts >= CallProcessingJob.max_attempts,
            CallProcessingJob.lease_expires_at < now_expr,
        )
        .values(
            status="dead_letter",
            claim_token=None,
            lease_expires_at=None,
            locked_by=None,
            last_error=reap_error,
            updated_at=now_expr,
        )
        .execution_options(synchronize_session=False)
    )
    res = db.execute(stmt)
    db.commit()
    rowcount = getattr(res, "rowcount", None)
    total_reaped = rowcount if isinstance(rowcount, int) and rowcount > 0 else 0

    if total_reaped > 0:
        for job_row in stale_jobs:
            report_dead_letter_transition(
                db=db,
                job_id=job_row.id,
                agent_call_id=job_row.agent_call_id,
                attempts=job_row.attempts,
                max_attempts=job_row.max_attempts,
                raw_error="Lease expired after reaching maximum attempts",
            )

    return total_reaped


def claim_next_job(
    db: Session,
    worker_id: str,
    job_type: str = "call_intelligence",
    lease_seconds: int = 300,
) -> Optional[ClaimedJob]:
    """
    Atomically claims the next eligible job using PostgreSQL SELECT ... FOR UPDATE SKIP LOCKED.
    Eligible jobs: attempts < max_attempts AND (pending with next_run_at <= NOW OR processing with expired lease).
    Immediately commits the claim transaction to release row lock.
    """
    # 1. First reap any expired jobs that have exhausted max_attempts
    reap_stale_dead_letter_jobs(db, job_type=job_type)

    dialect = get_dialect_name(db)
    now_expr = get_db_now(dialect)

    # 2. Query next eligible job
    query = (
        db.query(CallProcessingJob)
        .filter(
            CallProcessingJob.job_type == job_type,
            CallProcessingJob.attempts < CallProcessingJob.max_attempts,
            or_(
                and_(
                    CallProcessingJob.status == "pending",
                    CallProcessingJob.next_run_at <= now_expr,
                ),
                and_(
                    CallProcessingJob.status == "processing",
                    CallProcessingJob.lease_expires_at < now_expr,
                ),
            ),
        )
        .order_by(CallProcessingJob.next_run_at.asc())
    )

    if dialect == "postgresql":
        query = query.with_for_update(skip_locked=True)

    job = query.first()
    if not job:
        return None

    new_token = str(uuid.uuid4())
    future_expr = get_db_future_time(dialect, lease_seconds)
    new_attempts = job.attempts + 1

    # Atomic optimistic claim update fencing on pre-claim status & claim_token
    stmt = (
        update(CallProcessingJob)
        .where(
            CallProcessingJob.id == job.id,
            CallProcessingJob.status == job.status,
            CallProcessingJob.claim_token == job.claim_token,
        )
        .values(
            status="processing",
            attempts=new_attempts,
            claim_token=new_token,
            locked_by=worker_id,
            locked_at=now_expr,
            lease_expires_at=future_expr,
            updated_at=now_expr,
        )
        .execution_options(synchronize_session=False)
    )
    res = db.execute(stmt)
    rowcount = getattr(res, "rowcount", None)
    if not (isinstance(rowcount, int) and rowcount > 0):
        db.rollback()
        return None

    db.commit()

    return ClaimedJob(
        job_id=job.id,
        agent_call_id=job.agent_call_id,
        job_type=job.job_type,
        claim_token=new_token,
        attempts=new_attempts,
        max_attempts=job.max_attempts,
        locked_by=worker_id,
    )


def renew_job_lease(
    db: Session,
    job_id: int,
    claim_token: str,
    lease_seconds: int = 300,
) -> bool:
    """
    Fenced lease renewal (heartbeat).
    Requires matching id, claim_token, status='processing', and lease_expires_at > NOW().
    Returns True if lease was extended, False if fence was lost.
    """
    dialect = get_dialect_name(db)
    now_expr = get_db_now(dialect)
    future_expr = get_db_future_time(dialect, lease_seconds)

    stmt = (
        update(CallProcessingJob)
        .where(
            CallProcessingJob.id == job_id,
            CallProcessingJob.claim_token == claim_token,
            CallProcessingJob.status == "processing",
            CallProcessingJob.lease_expires_at > now_expr,
        )
        .values(
            lease_expires_at=future_expr,
            updated_at=now_expr,
        )
        .execution_options(synchronize_session=False)
    )
    res = db.execute(stmt)
    db.commit()
    rowcount = getattr(res, "rowcount", None)
    return isinstance(rowcount, int) and rowcount > 0


def complete_job(
    db: Session,
    job_id: int,
    claim_token: str,
    last_error: Optional[str] = None,
    auto_commit: bool = True,
) -> bool:
    """
    Fenced transition from 'processing' to 'completed'.
    Requires matching id, claim_token, status='processing', and lease_expires_at > NOW().
    Clears claim_token, lease_expires_at, and locked_by.
    """
    dialect = get_dialect_name(db)
    now_expr = get_db_now(dialect)

    stmt = (
        update(CallProcessingJob)
        .where(
            CallProcessingJob.id == job_id,
            CallProcessingJob.claim_token == claim_token,
            CallProcessingJob.status == "processing",
            CallProcessingJob.lease_expires_at > now_expr,
        )
        .values(
            status="completed",
            claim_token=None,
            lease_expires_at=None,
            locked_by=None,
            last_error=last_error,
            updated_at=now_expr,
        )
        .execution_options(synchronize_session=False)
    )
    res = db.execute(stmt)
    rowcount = getattr(res, "rowcount", None)
    success = isinstance(rowcount, int) and rowcount > 0
    if auto_commit:
        if success:
            db.commit()
        else:
            db.rollback()
    return success


def fail_job(
    db: Session,
    job_id: int,
    claim_token: str,
    attempts: int,
    max_attempts: int,
    error_message: str,
    is_retryable: bool = True,
    base_backoff_seconds: int = 30,
) -> bool:
    """
    Fenced failure transition.
    If attempts >= max_attempts or not is_retryable, transitions to 'dead_letter'.
    Otherwise, reschedules in 'pending' status with exponential backoff (30s, 60s, 120s).
    Requires matching id, claim_token, status='processing', and lease_expires_at > NOW().
    Emits structured dead-letter alert with suppression upon transition to dead_letter.
    """
    dialect = get_dialect_name(db)
    now_expr = get_db_now(dialect)

    is_dead_letter = attempts >= max_attempts or not is_retryable
    if is_dead_letter:
        new_status = "dead_letter"
        next_run = None
        saved_error = (
            error_message
            if DEAD_LETTER_ALERT_TAG in (error_message or "")
            else f"{DEAD_LETTER_ALERT_TAG} {error_message or ''}".strip()
        )
    else:
        new_status = "pending"
        # Exponential backoff formula: base_backoff_seconds * 2^(attempts-1)
        # Attempt 1 failed -> backoff = 30s
        # Attempt 2 failed -> backoff = 60s
        # Attempt 3 failed -> attempts (3) >= max_attempts (3) -> dead_letter
        backoff_seconds = base_backoff_seconds * (2 ** max(0, attempts - 1))
        next_run = get_db_future_time(dialect, backoff_seconds)
        saved_error = error_message or ""

    stmt = (
        update(CallProcessingJob)
        .where(
            CallProcessingJob.id == job_id,
            CallProcessingJob.claim_token == claim_token,
            CallProcessingJob.status == "processing",
            CallProcessingJob.lease_expires_at > now_expr,
        )
        .values(
            status=new_status,
            claim_token=None,
            lease_expires_at=None,
            locked_by=None,
            next_run_at=next_run if new_status == "pending" else CallProcessingJob.next_run_at,
            last_error=saved_error[:2000],
            updated_at=now_expr,
        )
        .execution_options(synchronize_session=False)
    )
    res = db.execute(stmt)
    db.commit()
    rowcount = getattr(res, "rowcount", None)
    success = isinstance(rowcount, int) and rowcount > 0

    if success and is_dead_letter:
        job_record = (
            db.query(CallProcessingJob.agent_call_id)
            .filter(CallProcessingJob.id == job_id)
            .first()
        )
        call_id = job_record[0] if job_record else 0
        report_dead_letter_transition(
            db=db,
            job_id=job_id,
            agent_call_id=call_id,
            attempts=attempts,
            max_attempts=max_attempts,
            raw_error=error_message,
        )

    return success


def _heartbeat_loop(
    job_id: int,
    claim_token: str,
    lease_seconds: int,
    interval_seconds: float,
    stop_event: threading.Event,
    abort_event: threading.Event,
    db_factory: Callable[[], Session],
):
    """
    Independent daemon thread performing heartbeat renewal.
    Uses its own isolated SessionLocal() per pulse. Never touches worker_db.
    """
    while not stop_event.wait(interval_seconds):
        if stop_event.is_set():
            break
        hb_db = db_factory()
        try:
            renewed = renew_job_lease(hb_db, job_id, claim_token, lease_seconds=lease_seconds)
            if not renewed:
                logger.warning("Heartbeat failed fence for job %s; signalling abort.", job_id)
                abort_event.set()
                break
        except Exception as exc:
            logger.error("Heartbeat exception for job %s: %s", job_id, exc)
            abort_event.set()
            break
        finally:
            hb_db.close()


def parse_caller_name(
    raw_name: Optional[str],
    direction: Optional[str] = "inbound",
) -> tuple[str, Optional[str]]:
    """
    Parse a caller name into (first_name, last_name).
    If no caller name is provided, use a truthful descriptive fallback
    ('Inbound Caller' or 'Outbound Contact') and never invent customer details.
    """
    if raw_name and raw_name.strip():
        parts = raw_name.strip().split(maxsplit=1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else None
        return first_name, last_name

    fallback = "Inbound Caller" if direction == "inbound" else "Outbound Contact"
    return fallback, None


def determine_lead_status_from_call(
    customer_intent: Optional[str] = None,
    lead_temperature: Optional[str] = None,
    call_outcome: Optional[str] = None,
    current_status: Optional[str] = None,
) -> str:
    """
    Determine the updated lead status based on customer intent, call outcome,
    and lead temperature. Intent and negative outcomes have higher priority.
    """
    intent = customer_intent.lower().strip() if customer_intent else ""
    outcome = call_outcome.lower().strip() if call_outcome else ""
    temp = lead_temperature.lower().strip() if lead_temperature else ""

    # 1. Negative / Not Interested signals
    if intent == "not_interested" or outcome in ("not interested", "not_interested"):
        return "lost"

    # 2. Strong Buying / Qualified signals
    if intent in ("high_purchase_intent", "purchase", "demo") or outcome in ("demo scheduled", "demo_scheduled"):
        return "qualified"

    # 3. Pricing / General Interest signals
    if intent == "pricing_interest" or outcome in ("interested", "pricing"):
        return "interested"

    # 4. Temperature / Follow-up signals
    if temp == "hot":
        return "qualified"
    if temp == "warm" or outcome in ("follow-up required", "follow_up_required", "follow_up", "follow up"):
        return "follow_up"
    if temp == "cold":
        return "cold"

    return current_status or "new"


def build_call_note_entry(
    agent_call_id: int,
    call_date_str: str,
    summary_text: Optional[str] = None,
    analysis: Optional[dict] = None,
    summary_data: Optional[dict] = None,
) -> str:
    """
    Construct a structured, formatted call intelligence note entry to append
    to a Lead's notes field.
    """
    call_tag = f"[AI Call #{agent_call_id} - {call_date_str}]"
    lines = [call_tag]

    if summary_text and summary_text.strip():
        lines.append(f"Summary: {summary_text.strip()}")

    if analysis:
        score = analysis.get("lead_score")
        temp = analysis.get("lead_temperature")
        intent = analysis.get("customer_intent")
        sentiment = analysis.get("sentiment")
        rec_action = analysis.get("recommended_action")

        metrics = []
        if score is not None:
            metrics.append(f"Score: {score}")
        if temp:
            metrics.append(f"Temp: {temp}")
        if intent:
            metrics.append(f"Intent: {intent}")
        if sentiment:
            metrics.append(f"Sentiment: {sentiment}")
        if metrics:
            lines.append("Metrics: " + " | ".join(metrics))

        if rec_action and rec_action.strip():
            lines.append(f"Action: {rec_action.strip()}")

    if summary_data:
        outcome = summary_data.get("outcome")
        next_action = summary_data.get("next_action")
        if outcome and (not analysis or outcome != analysis.get("customer_intent")):
            lines.append(f"Outcome: {outcome}")
        if next_action and (not analysis or next_action != analysis.get("recommended_action")):
            lines.append(f"Next Action: {next_action}")

    return "\n".join(lines)


def append_lead_note(
    existing_notes: Optional[str],
    new_entry: str,
    call_tag_prefix: str,
) -> str:
    """
    Safely append a note entry without duplicate repetitions for the same call.
    """
    if not existing_notes or not existing_notes.strip():
        return new_entry
    if call_tag_prefix in existing_notes:
        return existing_notes
    return f"{existing_notes.rstrip()}\n\n{new_entry}"


def build_task_description(
    summary_text: Optional[str],
    action_text: Optional[str],
    analysis: Optional[dict] = None,
) -> str:
    """
    Constructs an actionable task description with call context and metrics.
    """
    parts = []
    if action_text and action_text.strip():
        parts.append(f"Action: {action_text.strip()}")
    if summary_text and summary_text.strip():
        parts.append(f"Call Summary: {summary_text.strip()}")
    if analysis:
        score = analysis.get("lead_score")
        temp = analysis.get("lead_temperature")
        intent = analysis.get("customer_intent")
        metrics = []
        if score is not None:
            metrics.append(f"Score: {score}")
        if temp:
            metrics.append(f"Temp: {temp}")
        if intent:
            metrics.append(f"Intent: {intent}")
        if metrics:
            parts.append("Call Intelligence: " + " | ".join(metrics))
    return "\n\n".join(parts)


def detect_follow_up_action(
    transcript_text: Optional[str],
    analysis: Optional[dict] = None,
    summary_data: Optional[dict] = None,
    caller_display_name: str = "Customer",
) -> Optional[dict]:
    """
    Evaluates call intelligence, transcript, and summary to determine if a
    meaningful follow-up action is required. Returns a plan dictionary or None.
    Does NOT create tasks for negative/uninterested outcomes, empty transcripts,
    or calls lacking meaningful follow-up signals.
    """
    analysis = analysis or {}
    summary_data = summary_data or {}
    text_lower = (transcript_text or "").lower()

    outcome = summary_data.get("outcome") or ""
    outcome_lower = outcome.lower().strip()
    customer_intent = (analysis.get("customer_intent") or "").lower().strip()
    recommended_action = (analysis.get("recommended_action") or "").strip()
    next_action = (summary_data.get("next_action") or "").strip()

    # 1. Negative / Uninterested / Lost exclusions
    if customer_intent in ("not_interested", "lost"):
        return None
    if outcome_lower in ("not interested", "not_interested", "lost"):
        return None
    if any(phrase in text_lower for phrase in ["not interested", "stop calling", "do not call", "don't call"]):
        return None
    if "mark the lead as not interested" in next_action.lower():
        return None
    if "do not continue aggressive follow-up" in recommended_action.lower():
        return None

    summary_text = summary_data.get("summary") or ""
    default_due_days = 2
    if "tomorrow" in text_lower:
        default_due_days = 1

    # 2. Demo Request
    is_demo = (
        customer_intent in ("high_purchase_intent", "demo")
        or "demo" in text_lower
        or "demo" in next_action.lower()
        or "demo" in recommended_action.lower()
        or outcome_lower in ("demo scheduled", "demo_scheduled")
    )
    if is_demo:
        action_desc = recommended_action or next_action or "Follow up to schedule and conduct product demonstration."
        return {
            "title": f"Schedule Demo: {caller_display_name}",
            "description": build_task_description(summary_text, action_desc, analysis),
            "priority": "HIGH",
            "due_days": 1,
        }

    # 3. Callback Request
    callback_phrases = ["call me back", "call back", "callback", "call again", "reach back out", "ring me back", "give me a call"]
    is_callback = (
        any(phrase in text_lower for phrase in callback_phrases)
        or any(phrase in next_action.lower() for phrase in ["call back", "callback"])
    )
    if is_callback:
        action_desc = next_action or recommended_action or "Customer requested a callback. Contact customer to continue discussion."
        return {
            "title": f"Callback Request: {caller_display_name}",
            "description": build_task_description(summary_text, action_desc, analysis),
            "priority": "HIGH",
            "due_days": 1,
        }

    # 4. Pricing / Information Request
    is_pricing = (
        customer_intent == "pricing_interest"
        or "pricing" in outcome_lower
        or any(phrase in text_lower for phrase in ["pricing", "price", "quote", "cost", "how much does it cost"])
        or "pricing" in next_action.lower()
    )
    if is_pricing:
        action_desc = recommended_action or next_action or "Send requested pricing and plan options, then follow up."
        return {
            "title": f"Send Pricing Information: {caller_display_name}",
            "description": build_task_description(summary_text, action_desc, analysis),
            "priority": "MEDIUM",
            "due_days": default_due_days,
        }

    # 5. General Sales Follow-up / Explicit Next Action
    lead_temp = (analysis.get("lead_temperature") or "").lower().strip()
    is_follow_up_outcome = outcome_lower in ("follow-up required", "follow_up_required", "follow_up", "follow up", "interested")
    has_actionable_next_action = bool(next_action and "mark the lead as not interested" not in next_action.lower())

    if is_follow_up_outcome or lead_temp in ("hot", "warm") or has_actionable_next_action:
        action_desc = next_action or recommended_action or "Follow up with customer regarding sales inquiry."
        priority = "HIGH" if lead_temp == "hot" else "MEDIUM"
        due_days = 1 if lead_temp == "hot" else default_due_days
        return {
            "title": f"Follow-up: {caller_display_name}",
            "description": build_task_description(summary_text, action_desc, analysis),
            "priority": priority,
            "due_days": due_days,
        }

    # 6. No meaningful follow-up signal detected
    return None


def resolve_task_creator_id(
    db: Session,
    agent_call: AgentCall,
    matched_lead: Optional[Lead] = None,
    matched_contact: Optional[Contact] = None,
) -> int:
    """
    Resolves a valid User ID for Task.created_by, adhering to organization tenant isolation.
    """
    if matched_lead and matched_lead.owner_id:
        return matched_lead.owner_id
    if matched_contact and matched_contact.owner_id:
        return matched_contact.owner_id

    org_user = (
        db.query(User.id)
        .filter(User.organization_id == agent_call.organization_id)
        .order_by(User.id.asc())
        .first()
    )
    if org_user:
        return org_user[0]

    any_user = db.query(User.id).order_by(User.id.asc()).first()
    if any_user:
        return any_user[0]

    # Auto-provision system AI user for the organization if no user exists in DB
    sys_user = User(
        name="System AI",
        email=f"system_ai_org{agent_call.organization_id}@leadvoix.internal",
        hashed_password="system_internal_placeholder",
        organization_id=agent_call.organization_id,
        role="admin",
    )
    db.add(sys_user)
    db.flush()
    return sys_user.id


def process_claimed_job(
    claimed_job: ClaimedJob,
    worker_id: str,
    db_factory: Callable[[], Session] = SessionLocal,
    lease_seconds: int = 300,
    heartbeat_interval_seconds: float = 30.0,
) -> WorkerOutcome:
    """
    Executes the intelligence analysis for a claimed job with:
    1. AgentCall row lock & ownership validation.
    2. Independent heartbeat thread.
    3. Mandatory heartbeat shutdown confirmation before persistence.
    4. Atomic single-transaction persistence of Intelligence, Summary, and Fenced Job Completion.
    """
    worker_db = db_factory()
    try:
        # 1. Acquire exclusive row lock on AgentCall
        dialect = get_dialect_name(worker_db)
        call_query = worker_db.query(AgentCall).filter(AgentCall.id == claimed_job.agent_call_id)
        if dialect == "postgresql":
            call_query = call_query.with_for_update()
        agent_call = call_query.first()

        if not agent_call:
            worker_db.rollback()
            fail_job(
                worker_db,
                claimed_job.job_id,
                claimed_job.claim_token,
                claimed_job.attempts,
                claimed_job.max_attempts,
                f"AgentCall {claimed_job.agent_call_id} not found under lock",
                is_retryable=False,
            )
            return WorkerOutcome.NOT_ELIGIBLE

        # 2. Verify Agent and organization ownership
        agent = worker_db.query(Agent).filter(Agent.id == agent_call.agent_id).first()
        if not agent or agent_call.organization_id != agent.organization_id:
            worker_db.rollback()
            fail_job(
                worker_db,
                claimed_job.job_id,
                claimed_job.claim_token,
                claimed_job.attempts,
                claimed_job.max_attempts,
                "Agent or organization mismatch for call",
                is_retryable=False,
            )
            return WorkerOutcome.NOT_ELIGIBLE

        # 3. Verify status == 'completed'
        if agent_call.status != "completed":
            worker_db.rollback()
            fail_job(
                worker_db,
                claimed_job.job_id,
                claimed_job.claim_token,
                claimed_job.attempts,
                claimed_job.max_attempts,
                f"Call status '{agent_call.status}' is not completed",
                is_retryable=False,
            )
            return WorkerOutcome.NOT_ELIGIBLE

        # 4. Idempotency check: if intelligence already exists
        existing_intel = (
            worker_db.query(AgentCallIntelligence)
            .filter(AgentCallIntelligence.agent_call_id == agent_call.id)
            .first()
        )
        if existing_intel:
            fenced_ok = complete_job(
                worker_db,
                claimed_job.job_id,
                claimed_job.claim_token,
                last_error=None,
                auto_commit=True,
            )
            return WorkerOutcome.ALREADY_PROCESSED if fenced_ok else WorkerOutcome.FENCE_LOST

        # 5. Extract transcript
        transcript_text = build_transcript_text(worker_db, agent_call.id)
        if not transcript_text and agent_call.transcript:
            transcript_text = agent_call.transcript.strip()

        if not transcript_text:
            fenced_ok = complete_job(
                worker_db,
                claimed_job.job_id,
                claimed_job.claim_token,
                last_error="Empty transcript",
                auto_commit=True,
            )
            return WorkerOutcome.EMPTY_TRANSCRIPT if fenced_ok else WorkerOutcome.FENCE_LOST

        # 6. Start independent Heartbeat thread
        stop_heartbeat = threading.Event()
        abort_event = threading.Event()
        heartbeat_thread = threading.Thread(
            target=_heartbeat_loop,
            args=(
                claimed_job.job_id,
                claimed_job.claim_token,
                lease_seconds,
                heartbeat_interval_seconds,
                stop_heartbeat,
                abort_event,
                db_factory,
            ),
            daemon=True,
        )
        heartbeat_thread.start()

        # 7. Execute NLP Analysis
        try:
            analysis = analyze_call_intelligence(transcript_text)
            summary_data = analyze_call_transcript(transcript_text)
        except Exception as exc:
            stop_heartbeat.set()
            heartbeat_thread.join(timeout=3.0)
            worker_db.rollback()
            fail_job(
                worker_db,
                claimed_job.job_id,
                claimed_job.claim_token,
                claimed_job.attempts,
                claimed_job.max_attempts,
                f"Analysis exception: {type(exc).__name__}: {exc}",
                is_retryable=True,
            )
            return WorkerOutcome.RETRYABLE_FAILURE

        # 8. Check if heartbeat reported fence loss during analysis
        if abort_event.is_set():
            stop_heartbeat.set()
            heartbeat_thread.join(timeout=3.0)
            worker_db.rollback()
            logger.warning("Abort event detected for job %s; rolled back persistence.", claimed_job.job_id)
            return WorkerOutcome.FENCE_LOST

        # 9. Stop and confirm heartbeat thread termination (Mandatory Safeguard 3)
        stop_heartbeat.set()
        heartbeat_thread.join(timeout=3.0)
        if heartbeat_thread.is_alive():
            worker_db.rollback()
            logger.error(
                "Heartbeat thread failed to terminate within timeout for job %s; aborting persistence.",
                claimed_job.job_id,
            )
            return WorkerOutcome.FENCE_LOST

        # 10. Stage AgentCallIntelligence and AgentCallSummary in worker_db
        created_intelligence = AgentCallIntelligence(
            agent_call_id=agent_call.id,
            sentiment=analysis.get("sentiment"),
            lead_score=analysis.get("lead_score"),
            lead_temperature=analysis.get("lead_temperature"),
            customer_intent=analysis.get("customer_intent"),
            objections=analysis.get("objections"),
            buying_signals=analysis.get("buying_signals"),
            recommended_action=analysis.get("recommended_action"),
        )
        worker_db.add(created_intelligence)

        existing_summary = (
            worker_db.query(AgentCallSummary)
            .filter(AgentCallSummary.agent_call_id == agent_call.id)
            .first()
        )
        if not existing_summary:
            created_summary = AgentCallSummary(
                agent_call_id=agent_call.id,
                summary=summary_data.get("summary"),
                key_points=summary_data.get("key_points"),
                outcome=summary_data.get("outcome"),
                next_action=summary_data.get("next_action"),
            )
            worker_db.add(created_summary)

        # 10C. Idempotent CRM Contact / Lead Matching, Lead Creation & CRM Updates
        matched_contact: Optional[Contact] = None
        matched_lead: Optional[Lead] = None

        existing_activity = (
            worker_db.query(Activity)
            .filter(
                Activity.organization_id == agent_call.organization_id,
                Activity.agent_call_id == agent_call.id,
                Activity.activity_type == "call",
            )
            .first()
        )

        # If activity exists from previous attempt/retry, rehydrate contact or lead
        if existing_activity:
            if existing_activity.contact_id:
                matched_contact = (
                    worker_db.query(Contact)
                    .filter(
                        Contact.id == existing_activity.contact_id,
                        Contact.organization_id == agent_call.organization_id,
                    )
                    .first()
                )
            if existing_activity.lead_id:
                matched_lead = (
                    worker_db.query(Lead)
                    .filter(
                        Lead.id == existing_activity.lead_id,
                        Lead.organization_id == agent_call.organization_id,
                    )
                    .first()
                )

        caller_phone_norm = agent_call.caller_phone_normalized
        if not caller_phone_norm and agent_call.caller_phone:
            caller_phone_norm, _ = normalize_phone(agent_call.caller_phone)

        # If not resolved via existing_activity, match by normalized phone
        if not matched_contact and not matched_lead and caller_phone_norm:
            candidates = [caller_phone_norm]
            if caller_phone_norm.startswith("+"):
                candidates.append(caller_phone_norm.lstrip("+"))
            else:
                candidates.append(f"+{caller_phone_norm}")

            # 1. Resolve Contact first within the same organization
            matched_contact = (
                worker_db.query(Contact)
                .filter(
                    Contact.organization_id == agent_call.organization_id,
                    Contact.phone_normalized.in_(candidates),
                )
                .first()
            )

            # 2. If no Contact matches, resolve Lead within the same organization
            if not matched_contact:
                matched_lead = (
                    worker_db.query(Lead)
                    .filter(
                        Lead.organization_id == agent_call.organization_id,
                        Lead.phone_normalized.in_(candidates),
                    )
                    .first()
                )

        # 3. If neither Contact nor Lead matched, create a new Lead
        if not matched_contact and not matched_lead:
            first_name, last_name = parse_caller_name(
                agent_call.caller_name,
                agent_call.direction,
            )
            matched_lead = Lead(
                first_name=first_name,
                last_name=last_name,
                phone=agent_call.caller_phone,
                phone_normalized=caller_phone_norm,
                phone_extension=agent_call.caller_phone_extension,
                source="ai_voice_call",
                status="new",
                organization_id=agent_call.organization_id,
            )
            worker_db.add(matched_lead)
            worker_db.flush()

        # 4. If matched_contact has a linked lead_id, also resolve that linked lead
        target_lead_to_update = matched_lead
        if not target_lead_to_update and matched_contact and matched_contact.lead_id:
            target_lead_to_update = (
                worker_db.query(Lead)
                .filter(
                    Lead.id == matched_contact.lead_id,
                    Lead.organization_id == agent_call.organization_id,
                )
                .first()
            )

        # 5. Update Lead status and append structured call intelligence notes
        if target_lead_to_update:
            call_outcome = summary_data.get("outcome") if summary_data else None
            cust_intent = analysis.get("customer_intent") if analysis else None
            lead_temp = analysis.get("lead_temperature") if analysis else None

            new_status = determine_lead_status_from_call(
                customer_intent=cust_intent,
                lead_temperature=lead_temp,
                call_outcome=call_outcome,
                current_status=target_lead_to_update.status,
            )
            target_lead_to_update.status = new_status

            call_date_str = (
                agent_call.started_at.strftime("%Y-%m-%d %H:%M:%S")
                if agent_call.started_at
                else datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            )
            call_tag_prefix = f"[AI Call #{agent_call.id}"
            note_entry = build_call_note_entry(
                agent_call_id=agent_call.id,
                call_date_str=call_date_str,
                summary_text=summary_data.get("summary") if summary_data else None,
                analysis=analysis,
                summary_data=summary_data,
            )
            target_lead_to_update.notes = append_lead_note(
                target_lead_to_update.notes,
                note_entry,
                call_tag_prefix,
            )
            target_lead_to_update.updated_at = datetime.now(timezone.utc)

        # 6. Resolve caller display name for CRM Activity and Follow-up Task
        caller_display_name = (
            f"{matched_contact.first_name} {matched_contact.last_name or ''}".strip()
            if matched_contact
            else (
                f"{matched_lead.first_name} {matched_lead.last_name or ''}".strip()
                if matched_lead
                else (
                    f"{target_lead_to_update.first_name} {target_lead_to_update.last_name or ''}".strip()
                    if target_lead_to_update
                    else (agent_call.caller_name or "Unknown")
                )
            )
        )

        # Create Activity if not already created
        if not existing_activity:
            meta = {
                "sentiment": analysis.get("sentiment"),
                "lead_score": analysis.get("lead_score"),
                "lead_temperature": analysis.get("lead_temperature"),
                "duration": agent_call.duration,
                "call_status": agent_call.status,
            }
            created_activity = Activity(
                organization_id=agent_call.organization_id,
                activity_type="call",
                title=f"AI Voice Call - {caller_display_name}",
                content=(summary_data.get("summary") if summary_data else None) or "AI Voice Call processed",
                metadata_json=json.dumps(meta),
                agent_call_id=agent_call.id,
                contact_id=matched_contact.id if matched_contact else None,
                lead_id=matched_lead.id if matched_lead else (target_lead_to_update.id if target_lead_to_update else None),
                user_id=None,
            )
            worker_db.add(created_activity)

        # 10D. Idempotent CRM Follow-up Task Creation
        existing_task: Optional[Task] = None
        created_task: Optional[Task] = None
        follow_up_plan = detect_follow_up_action(
            transcript_text=transcript_text,
            analysis=analysis,
            summary_data=summary_data,
            caller_display_name=caller_display_name,
        )

        if follow_up_plan:
            existing_task = (
                worker_db.query(Task)
                .filter(
                    Task.organization_id == agent_call.organization_id,
                    Task.agent_call_id == agent_call.id,
                )
                .first()
            )
            if not existing_task:
                effective_lead = matched_lead or target_lead_to_update
                creator_id = resolve_task_creator_id(
                    db=worker_db,
                    agent_call=agent_call,
                    matched_lead=effective_lead,
                    matched_contact=matched_contact,
                )
                assigned_to = (
                    (effective_lead.owner_id if effective_lead else None)
                    or (matched_contact.owner_id if matched_contact else None)
                    or creator_id
                )
                due_date_val = (
                    datetime.now(timezone.utc) + timedelta(days=follow_up_plan["due_days"])
                ).date()

                company_id_val = None
                if effective_lead and effective_lead.company_id:
                    company_id_val = effective_lead.company_id
                elif matched_contact and matched_contact.company_id:
                    company_id_val = matched_contact.company_id

                created_task = Task(
                    title=follow_up_plan["title"],
                    description=follow_up_plan["description"],
                    priority=follow_up_plan["priority"],
                    status="TODO",
                    due_date=due_date_val,
                    organization_id=agent_call.organization_id,
                    agent_call_id=agent_call.id,
                    lead_id=effective_lead.id if effective_lead else None,
                    contact_id=matched_contact.id if matched_contact else None,
                    deal_id=None,
                    company_id=company_id_val,
                    assigned_to=assigned_to,
                    created_by=creator_id,
                )
                worker_db.add(created_task)

        # 10E. Automatic CRM Pipeline & Deal Automation
        created_deal = automate_pipeline_and_deal(
            db=worker_db,
            organization_id=agent_call.organization_id,
            agent_call=agent_call,
            analysis=analysis,
            summary_data=summary_data,
            matched_lead=matched_lead or target_lead_to_update,
            matched_contact=matched_contact,
            caller_display_name=caller_display_name,
            auto_commit=False,
        )

        # Link Task to Deal if both exist
        if created_deal:
            task_to_link = created_task or existing_task
            if task_to_link and not task_to_link.deal_id:
                task_to_link.deal_id = created_deal.id

        # 11. Execute fenced completion in the SAME transaction (Mandatory Safeguard 4 & 5)
        fence_ok = complete_job(
            worker_db,
            claimed_job.job_id,
            claimed_job.claim_token,
            last_error=None,
            auto_commit=False,
        )

        if not fence_ok:
            worker_db.rollback()
            logger.warning(
                "Fenced completion failed (fence lost) for job %s; rolled back all persistence.",
                claimed_job.job_id,
            )
            return WorkerOutcome.FENCE_LOST

        # 12. Single Atomic Commit
        worker_db.commit()
        logger.info(
            "Job %s successfully processed and atomically committed with intelligence & summary.",
            claimed_job.job_id,
        )
        return WorkerOutcome.SUCCESS

    except Exception as exc:
        worker_db.rollback()
        logger.error(
            "Unexpected error in process_claimed_job for job %s: %s",
            claimed_job.job_id,
            exc,
        )
        fail_job(
            worker_db,
            claimed_job.job_id,
            claimed_job.claim_token,
            claimed_job.attempts,
            claimed_job.max_attempts,
            f"Unexpected error: {type(exc).__name__}: {exc}",
            is_retryable=True,
        )
        return WorkerOutcome.RETRYABLE_FAILURE
    finally:
        worker_db.close()


def run_worker_cycle(
    worker_id: str,
    db_factory: Callable[[], Session] = SessionLocal,
    job_type: str = "call_intelligence",
    lease_seconds: int = 300,
    heartbeat_interval_seconds: float = 30.0,
) -> WorkerOutcome:
    """
    Executes one complete claim-execute cycle.
    Returns NO_JOB_AVAILABLE if no job was claimed.
    """
    claim_db = db_factory()
    try:
        claimed = claim_next_job(
            claim_db,
            worker_id=worker_id,
            job_type=job_type,
            lease_seconds=lease_seconds,
        )
    finally:
        claim_db.close()

    if not claimed:
        return WorkerOutcome.NO_JOB_AVAILABLE

    return process_claimed_job(
        claimed,
        worker_id=worker_id,
        db_factory=db_factory,
        lease_seconds=lease_seconds,
        heartbeat_interval_seconds=heartbeat_interval_seconds,
    )
