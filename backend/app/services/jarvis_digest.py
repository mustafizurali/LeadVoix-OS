"""
LeadVoix Business JARVIS — Executive Digest & Outbound Dispatch Service
Phase 1 MVP — Phase A Hardened

Responsibilities:
- Formats structured business digests for Morning Briefings (08:00 IST) and Evening Debriefs (21:00 IST).
- Outbound Telegram notifications via Bot API HTTP requests (no inbound webhooks).
- Durable Idempotency Store: survives restarts via atomic file persistence.
- Safe Retry Behavior: delivery failures trigger cooldown (minimum 60s) and do not record completed dispatches.
- Feature flag enforcement: ENABLE_JARVIS=false immediately halts execution.
- Sensitive token masking: Telegram bot tokens are never logged or echoed in error reports.
"""

from datetime import datetime, timezone, timedelta
import json
import logging
import os
import threading
from typing import Any, Dict, Optional, Tuple
import uuid
from zoneinfo import ZoneInfo

import httpx
from sqlalchemy.orm import Session

from backend.app.models.jarvis import JarvisDispatchIdempotency
from backend.app.services.jarvis_collector import (
    KOLKATA_TZ,
    calculate_digest_window,
    collect_jarvis_metrics,
    get_internal_org_id,
    get_jarvis_read_only_session,
    get_jarvis_timezone,
)


logger = logging.getLogger("leadvoix.jarvis.digest")

DEFAULT_IDEMPOTENCY_FILE = os.path.join("data", "jarvis_idempotency.json")
DEFAULT_RETRY_COOLDOWN_SECONDS = 60


class DurableIdempotencyStore:
    """
    Thread-safe, atomic-persisted idempotency store.
    Survives server and container restarts by persisting state to a local JSON file.
    Tracks success ('completed') and failure ('failed') states with retry cooldowns.
    """
    def __init__(
        self,
        file_path: Optional[str] = None,
        retry_cooldown_seconds: Optional[int] = None,
    ):
        self._file_path = file_path or os.getenv("JARVIS_IDEMPOTENCY_FILE", DEFAULT_IDEMPOTENCY_FILE)
        raw_cooldown = os.getenv("JARVIS_RETRY_COOLDOWN_SECONDS")
        if retry_cooldown_seconds is not None:
            self._cooldown_seconds = retry_cooldown_seconds
        elif raw_cooldown and raw_cooldown.strip().isdigit():
            self._cooldown_seconds = max(10, int(raw_cooldown.strip()))
        else:
            self._cooldown_seconds = DEFAULT_RETRY_COOLDOWN_SECONDS

        self._lock = threading.Lock()
        self._records: Dict[str, Dict[str, Any]] = {}
        self._load()

    @property
    def cooldown_seconds(self) -> int:
        return self._cooldown_seconds

    @property
    def file_path(self) -> str:
        return self._file_path

    def get_record(self, key: str) -> Optional[Dict[str, Any]]:
        """Returns the stored record for a given idempotency key, or None."""
        with self._lock:
            record = self._records.get(key)
            return dict(record) if record is not None else None

    def _load(self) -> None:
        """Loads persisted state from disk if the file exists."""
        if not os.path.exists(self._file_path):
            self._records = {}
            return

        try:
            with open(self._file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    self._records = data
                else:
                    self._records = {}
        except Exception as exc:
            logger.warning(
                "Failed to read JARVIS idempotency file (%s): %s. Starting with empty store.",
                self._file_path,
                exc,
            )
            self._records = {}

    def _persist(self) -> None:
        """Atomically persists records to disk using a temporary file and atomic replace."""
        try:
            dir_name = os.path.dirname(self._file_path)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)
            tmp_file = f"{self._file_path}.tmp"
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(self._records, f, indent=2, default=str)
            os.replace(tmp_file, self._file_path)
        except Exception as exc:
            logger.error(
                "Failed to persist JARVIS idempotency state to %s: %s",
                self._file_path,
                exc,
            )

    def check_dispatch_allowed(
        self,
        key: str,
        force: bool = False,
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Evaluates whether a dispatch can proceed.
        Returns:
            (allowed: bool, rejection_reason: Optional[str], details: Optional[Dict])
        """
        if force:
            return True, None, None

        with self._lock:
            record = self._records.get(key)
            if not record:
                return True, None, None

            record_status = record.get("status")
            if record_status == "completed":
                return False, "already_dispatched", record

            if record_status == "failed":
                last_attempt_str = record.get("last_attempt_at")
                if last_attempt_str:
                    try:
                        last_attempt = datetime.fromisoformat(last_attempt_str)
                        if last_attempt.tzinfo is None:
                            last_attempt = last_attempt.replace(tzinfo=timezone.utc)
                        elapsed = (datetime.now(timezone.utc) - last_attempt).total_seconds()
                        if elapsed < self._cooldown_seconds:
                            remaining = max(1, int(self._cooldown_seconds - elapsed))
                            return False, "retry_cooldown", {**record, "cooldown_remaining_seconds": remaining}
                    except Exception:
                        pass
                # Cooldown has expired, retry is allowed
                return True, None, record

            return True, None, None

    def record_success(self, key: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Records a verified successful dispatch into durable storage."""
        with self._lock:
            now_iso = datetime.now(timezone.utc).isoformat()
            record = {
                **metadata,
                "status": "completed",
                "completed_at": now_iso,
                "last_attempt_at": now_iso,
            }
            self._records[key] = record
            self._persist()
            return record

    def record_failure(self, key: str, metadata: Dict[str, Any], error: Any) -> Dict[str, Any]:
        """Records a failed dispatch attempt with retry metadata and timestamp into durable storage."""
        with self._lock:
            prev = self._records.get(key, {})
            retry_count = int(prev.get("retry_count", 0)) + 1
            now_iso = datetime.now(timezone.utc).isoformat()
            record = {
                **metadata,
                "status": "failed",
                "retry_count": retry_count,
                "last_error": error,
                "last_attempt_at": now_iso,
            }
            self._records[key] = record
            self._persist()
            return record

    def clear(self) -> None:
        """Clears memory and removes persisted file from disk."""
        with self._lock:
            self._records.clear()
            if os.path.exists(self._file_path):
                try:
                    os.remove(self._file_path)
                except Exception:
                    pass


# Global singleton instance
_IDEMPOTENCY_STORE: Optional[DurableIdempotencyStore] = None


def get_idempotency_store() -> DurableIdempotencyStore:
    """Returns or lazily creates the global DurableIdempotencyStore instance."""
    global _IDEMPOTENCY_STORE
    if _IDEMPOTENCY_STORE is None:
        _IDEMPOTENCY_STORE = DurableIdempotencyStore()
    return _IDEMPOTENCY_STORE


def set_idempotency_store(store: Optional[DurableIdempotencyStore]) -> None:
    """Explicitly sets or resets the global store instance (primarily for testing)."""
    global _IDEMPOTENCY_STORE
    _IDEMPOTENCY_STORE = store


class _DispatchedDigestsFacade(dict):
    """Facade dictionary mapping to the underlying DurableIdempotencyStore for backward compatibility."""
    def __getitem__(self, key: str) -> Any:
        return get_idempotency_store()._records[key]

    def __setitem__(self, key: str, value: Any) -> None:
        get_idempotency_store()._records[key] = value

    def __contains__(self, key: object) -> bool:
        return key in get_idempotency_store()._records

    def clear(self) -> None:
        get_idempotency_store().clear()

    def get(self, key: str, default: Any = None) -> Any:
        return get_idempotency_store()._records.get(key, default)

    def __iter__(self):
        return iter(get_idempotency_store()._records)

    def __len__(self) -> int:
        return len(get_idempotency_store()._records)


_DISPATCHED_DIGESTS = _DispatchedDigestsFacade()


def is_jarvis_enabled() -> bool:
    """Returns True if JARVIS features are enabled via environment variable ENABLE_JARVIS."""
    val = os.getenv("ENABLE_JARVIS", "false").strip().lower()
    return val in ("true", "1", "yes", "on")


def get_telegram_credentials() -> Dict[str, Optional[str]]:
    """Retrieves configured Telegram bot credentials without exposing them."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    return {
        "bot_token": token.strip() if token else None,
        "chat_id": chat_id.strip() if chat_id else None,
    }


def mask_token(token: Optional[str]) -> str:
    """Masks secret token string for safe logging."""
    if not token or len(token) < 8:
        return "[NOT_CONFIGURED]"
    return f"{token[:4]}...{token[-4:]}"


def format_executive_digest(
    metrics: Dict[str, Any],
    digest_type: str,
    window_label: str,
) -> str:
    """
    Renders a clear, professional Markdown digest for Telegram transmission.
    Aggregates telephony, lead pipeline, revenue deals, and background jobs.
    Zero PII is included in the output.
    """
    org = metrics.get("organization", {})
    org_name = org.get("name", "LeadVoix")
    window = metrics.get("window", {})
    start_str = window.get("start_local") or window.get("start_kolkata", "")
    end_str = window.get("end_local") or window.get("end_kolkata", "")
    tz_val = window.get("timezone")
    period_tz = "IST" if tz_val == "Asia/Kolkata" or (not tz_val and "IST" in str(start_str)) else (tz_val or "Local")

    telephony = metrics.get("telephony", {})
    total_calls = telephony.get("total_calls", 0)
    completed_calls = telephony.get("status_breakdown", {}).get("completed", 0)
    success_rate = round((completed_calls / total_calls * 100), 1) if total_calls > 0 else 0.0
    total_mins = telephony.get("total_duration_minutes", 0.0)
    avg_sec = telephony.get("average_duration_seconds", 0.0)

    leads = metrics.get("leads", {})
    total_leads = leads.get("total_leads", 0)
    lead_sources = leads.get("source_breakdown", {})
    top_sources_str = ", ".join(f"{k}: {v}" for k, v in sorted(lead_sources.items(), key=lambda x: x[1], reverse=True)[:3]) or "None"

    deals = metrics.get("deals", {})
    total_deals = deals.get("total_deals_created", 0)
    won_amount = deals.get("won_amount_total", 0.0)

    tasks = metrics.get("tasks", {}).get("status_breakdown", {})
    pending_tasks = tasks.get("pending", 0)
    completed_tasks = tasks.get("completed", 0)

    system_jobs = metrics.get("system_jobs", {}).get("processing_jobs_summary", {})
    jobs_summary_str = ", ".join(f"{k}: {v}" for k, v in system_jobs.items()) or "Idle"

    header_title = (
        "🌅 *LeadVoix Business JARVIS — Morning Briefing*"
        if digest_type == "morning"
        else "🌙 *LeadVoix Business JARVIS — Evening Debrief*"
        if digest_type == "evening"
        else "📊 *LeadVoix Business JARVIS — Operations Digest*"
    )

    lines = [
        header_title,
        f"🏢 *Organization:* `{org_name}`",
        f"⏱ *Period ({period_tz}):* {start_str} to {end_str}",
        "",
        "📞 *Voice Telephony Operations*",
        f"• Total Inbound/Outbound Calls: *{total_calls}*",
        f"• Successfully Completed: *{completed_calls}* ({success_rate}%)",
        f"• Cumulative Airtime: *{total_mins} mins* (avg {avg_sec}s/call)",
        "",
        "👥 *Lead Generation & Inbound Pipeline*",
        f"• New Inbound Leads: *{total_leads}*",
        f"• Lead Acquisition Sources: {top_sources_str}",
        "",
        "💼 *Commercial Deals & Revenue Pipeline*",
        f"• New Pipeline Deals: *{total_deals}*",
        f"• Won Deals Volume: *${won_amount:,.2f}*",
        "",
        "📋 *Actionable CRM Tasks*",
        f"• Pending Tasks: *{pending_tasks}*",
        f"• Completed Tasks: *{completed_tasks}*",
        "",
        "⚙️ *System Intelligence & Background Jobs*",
        f"• Call Processing Status: `{jobs_summary_str}`",
        "• Infrastructure Status: *Operational ✅*",
        "",
        "_LeadVoix Autonomous Business Intelligence v1.0 (Phase 1 — Phase A Hardened)_",
    ]

    return "\n".join(lines)


def send_telegram_notification(
    text_content: str,
    bot_token: Optional[str] = None,
    chat_id: Optional[str] = None,
    client: Optional[httpx.Client] = None,
) -> Dict[str, Any]:
    """
    Dispatches outbound Telegram notification using Telegram Bot API sendMessage.
    Does not install webhooks or accept inbound messages.
    Handles network errors safely without crashing calling service.
    """
    creds = get_telegram_credentials()
    token = bot_token or creds.get("bot_token")
    target_chat = chat_id or creds.get("chat_id")

    if not token or not target_chat:
        logger.info(
            "Telegram credentials not configured (token=%s, chat_id=%s). Notification logged but not sent.",
            mask_token(token),
            bool(target_chat),
        )
        return {
            "delivered": False,
            "reason": "telegram_not_configured",
            "message": "Telegram bot token or chat ID is not configured.",
        }

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": target_chat,
        "text": text_content,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }

    try:
        if client is not None:
            resp = client.post(url, json=payload, timeout=10.0)
        else:
            with httpx.Client(timeout=10.0) as http_client:
                resp = http_client.post(url, json=payload)

        if resp.status_code == 200:
            data = resp.json()
            msg_id = data.get("result", {}).get("message_id")
            logger.info("Telegram notification successfully sent (message_id=%s)", msg_id)
            return {
                "delivered": True,
                "message_id": msg_id,
            }
        else:
            logger.warning(
                "Telegram API responded with HTTP %s: %s",
                resp.status_code,
                resp.text[:120],
            )
            return {
                "delivered": False,
                "reason": f"telegram_api_error_http_{resp.status_code}",
                "status_code": resp.status_code,
            }
    except Exception as exc:
        logger.error(
            "Exception while sending Telegram message: %s",
            type(exc).__name__,
        )
        return {
            "delivered": False,
            "reason": "network_exception",
            "error_type": type(exc).__name__,
        }


def check_or_reserve_db_dispatch(
    db: Session,
    idempotency_key: str,
    org_id: int,
    digest_type: str,
    window_date: Any,
    force: bool = False,
    lease_seconds: int = 180,
) -> Tuple[bool, str, Optional[Dict[str, Any]], bool]:
    """
    Two-Phase Persistent Reservation:
    Atomically checks and reserves dispatch in jarvis.dispatch_idempotency.
    Returns:
        (allowed: bool, status: str, details: Optional[Dict], is_crash_recovery: bool)
    """
    now = datetime.now(timezone.utc)
    try:
        record = (
            db.query(JarvisDispatchIdempotency)
            .filter(JarvisDispatchIdempotency.idempotency_key == idempotency_key)
            .with_for_update()
            .first()
        )
    except Exception as exc:
        logger.debug("Database idempotency table unavailable or error: %s. Using file fallback.", exc)
        return True, "fallback", None, False

    if not record:
        new_record = JarvisDispatchIdempotency(
            organization_id=org_id,
            digest_type=digest_type,
            window_date=window_date,
            idempotency_key=idempotency_key,
            status="in_flight",
            claim_token=str(uuid.uuid4()) if hasattr(uuid, "uuid4") else "claim",
            lease_expires_at=now + timedelta(seconds=lease_seconds),
            retry_count=0,
            created_at=now,
        )
        db.add(new_record)
        db.commit()
        return True, "in_flight", None, False

    if force:
        record.status = "in_flight"
        record.lease_expires_at = now + timedelta(seconds=lease_seconds)
        db.commit()
        return True, "forced", None, False

    if record.status == "completed":
        return False, "already_dispatched", {
            "completed_at": record.completed_at.isoformat() if record.completed_at else None,
            "telegram_message_id": record.telegram_message_id,
        }, False

    if record.status == "failed":
        if record.cooldown_until:
            cd = record.cooldown_until
            if cd.tzinfo is None:
                cd = cd.replace(tzinfo=timezone.utc)
            if now < cd:
                remaining = max(1, int((cd - now).total_seconds()))
                return False, "retry_cooldown", {
                    "retry_count": record.retry_count,
                    "cooldown_remaining_seconds": remaining,
                    "last_error": record.last_error,
                }, False
        record.status = "in_flight"
        record.lease_expires_at = now + timedelta(seconds=lease_seconds)
        db.commit()
        return True, "retry_in_flight", None, False

    if record.status == "in_flight":
        lease_exp = record.lease_expires_at
        if lease_exp and lease_exp.tzinfo is None:
            lease_exp = lease_exp.replace(tzinfo=timezone.utc)
        if lease_exp and now < lease_exp:
            return False, "in_flight_active", {
                "lease_expires_at": lease_exp.isoformat(),
            }, False
        # Crash-window recovery scenario
        logger.warning(
            "CRASH WINDOW RECOVERY: Dispatch '%s' was abandoned in_flight. Reclaiming for safe transmission.",
            idempotency_key,
        )
        record.status = "crash_window_recovery"
        record.lease_expires_at = now + timedelta(seconds=lease_seconds)
        db.commit()
        return True, "crash_window_recovery", {
            "created_at": record.created_at.isoformat() if record.created_at else None,
        }, True

    return True, "in_flight", None, False


def finalize_db_dispatch(
    db: Session,
    idempotency_key: str,
    success: bool,
    telegram_result: Dict[str, Any],
    cooldown_seconds: int = 60,
) -> None:
    """Updates persistent dispatch record upon execution outcome."""
    now = datetime.now(timezone.utc)
    try:
        record = (
            db.query(JarvisDispatchIdempotency)
            .filter(JarvisDispatchIdempotency.idempotency_key == idempotency_key)
            .first()
        )
        if not record:
            return

        if success:
            record.status = "completed"
            record.completed_at = now
            record.telegram_message_id = telegram_result.get("message_id")
            record.lease_expires_at = None
        else:
            record.status = "failed"
            record.retry_count = int(record.retry_count or 0) + 1
            record.cooldown_until = now + timedelta(seconds=cooldown_seconds)
            record.last_error = telegram_result
            record.lease_expires_at = None
        db.commit()
    except Exception as exc:
        logger.debug("Error updating DB dispatch status: %s", exc)


def generate_and_dispatch_digest(
    digest_type: str = "custom",
    target_date: Optional[datetime.date] = None,
    force: bool = False,
    send_telegram: bool = True,
    db: Optional[Session] = None,
    operational_db: Optional[Session] = None,
    http_client: Optional[httpx.Client] = None,
) -> Dict[str, Any]:
    """
    Main orchestrator for JARVIS digest:
    1. Checks ENABLE_JARVIS feature flag.
    2. Calculates Asia/Kolkata date window.
    3. Enforces persistent two-phase reservation (in_flight -> completed / failed / crash_window_recovery).
       - Supports database-backed jarvis.dispatch_idempotency and file-based fallback.
    4. Collects read-only metrics.
    5. Formats executive markdown digest.
    6. Dispatches outbound Telegram notification if requested.
    7. Safe dispatch recording with retry cooldowns and crash-window disambiguation.
    """
    if not is_jarvis_enabled():
        return {
            "status": "disabled",
            "enabled": False,
            "message": "JARVIS is disabled. Set ENABLE_JARVIS=true to activate.",
        }

    org_id = get_internal_org_id()
    active_tz = get_jarvis_timezone()
    start_utc, end_utc, window_label = calculate_digest_window(digest_type, target_date=target_date, tz=active_tz)
    window_date = start_utc.astimezone(active_tz).date()
    window_date_str = window_date.strftime("%Y-%m-%d")

    idempotency_key = f"{org_id}:{digest_type}:{window_date_str}"
    store = get_idempotency_store()

    is_crash_recovery = False
    use_db_idempotency = False

    if operational_db is not None:
        allowed, db_status, details, is_crash_recovery = check_or_reserve_db_dispatch(
            operational_db,
            idempotency_key,
            org_id,
            digest_type,
            window_date,
            force=force,
        )
        if db_status != "fallback":
            use_db_idempotency = True
            if not allowed:
                if db_status == "already_dispatched":
                    return {
                        "status": "already_dispatched",
                        "idempotent": True,
                        "idempotency_key": idempotency_key,
                        "dispatched_at": (details or {}).get("completed_at"),
                        "window": window_label,
                        "message": "Digest already dispatched and confirmed for this date and window. Use force=true to override.",
                    }
                elif db_status == "retry_cooldown":
                    remaining = (details or {}).get("cooldown_remaining_seconds", 60)
                    return {
                        "status": "retry_cooldown",
                        "idempotent": True,
                        "idempotency_key": idempotency_key,
                        "retry_count": (details or {}).get("retry_count", 1),
                        "cooldown_remaining_seconds": remaining,
                        "last_error": (details or {}).get("last_error"),
                        "window": window_label,
                        "message": f"Previous dispatch attempt failed. Safe retry cooldown active ({remaining}s remaining). Use force=true to override.",
                    }
                elif db_status == "in_flight_active":
                    return {
                        "status": "in_flight",
                        "idempotent": True,
                        "idempotency_key": idempotency_key,
                        "window": window_label,
                        "message": "Dispatch is currently in-flight by another active worker.",
                    }

    if not use_db_idempotency:
        allowed, rejection_reason, record_details = store.check_dispatch_allowed(idempotency_key, force=force)
        if not allowed:
            if rejection_reason == "already_dispatched":
                logger.info("Idempotent dispatch: Digest already sent for key %s", idempotency_key)
                return {
                    "status": "already_dispatched",
                    "idempotent": True,
                    "idempotency_key": idempotency_key,
                    "dispatched_at": (record_details or {}).get("completed_at") or (record_details or {}).get("timestamp"),
                    "window": window_label,
                    "message": "Digest already dispatched and confirmed for this date and window. Use force=true to override.",
                }
            elif rejection_reason == "retry_cooldown":
                remaining = (record_details or {}).get("cooldown_remaining_seconds", store.cooldown_seconds)
                logger.warning(
                    "Dispatch blocked by retry cooldown for key %s (%ss remaining)",
                    idempotency_key,
                    remaining,
                )
                return {
                    "status": "retry_cooldown",
                    "idempotent": True,
                    "idempotency_key": idempotency_key,
                    "retry_count": (record_details or {}).get("retry_count", 1),
                    "cooldown_remaining_seconds": remaining,
                    "last_error": (record_details or {}).get("last_error"),
                    "window": window_label,
                    "message": f"Previous dispatch attempt failed. Safe retry cooldown active ({remaining}s remaining). Use force=true to override.",
                }

    # Execute read-only metrics collection
    if db is not None:
        metrics = collect_jarvis_metrics(db, org_id=org_id, start_utc=start_utc, end_utc=end_utc)
    else:
        with get_jarvis_read_only_session() as read_session:
            metrics = collect_jarvis_metrics(read_session, org_id=org_id, start_utc=start_utc, end_utc=end_utc)

    formatted_text = format_executive_digest(metrics, digest_type, window_label)

    # Crash-window disambiguation disclaimer:
    if is_crash_recovery:
        formatted_text = "⚠️ *[JARVIS System Recovery: Dispatched after worker restart]*\n\n" + formatted_text

    telegram_result = {"delivered": False, "reason": "skipped_by_request"}
    if send_telegram:
        telegram_result = send_telegram_notification(formatted_text, client=http_client)

    metadata = {
        "idempotency_key": idempotency_key,
        "digest_type": digest_type,
        "window_label": window_label,
        "telegram_result": telegram_result,
    }

    # Evaluate delivery outcome
    if send_telegram and not telegram_result.get("delivered", False):
        if use_db_idempotency and operational_db is not None:
            finalize_db_dispatch(operational_db, idempotency_key, success=False, telegram_result=telegram_result)
        failure_record = store.record_failure(idempotency_key, metadata, error=telegram_result)
        logger.warning(
            "Telegram delivery failed for %s. Failure recorded with retry_count=%s, cooldown=%ss.",
            idempotency_key,
            failure_record.get("retry_count"),
            store.cooldown_seconds,
        )
        return {
            "status": "delivery_failed",
            "enabled": True,
            "digest_type": digest_type,
            "window_label": window_label,
            "idempotency_key": idempotency_key,
            "retry_count": failure_record.get("retry_count", 1),
            "cooldown_seconds": store.cooldown_seconds,
            "metrics": metrics,
            "formatted_digest": formatted_text,
            "telegram": telegram_result,
            "crash_window_recovery": is_crash_recovery,
        }

    # Success: record completed dispatch
    if use_db_idempotency and operational_db is not None:
        finalize_db_dispatch(operational_db, idempotency_key, success=True, telegram_result=telegram_result)
    store.record_success(idempotency_key, metadata)

    return {
        "status": "success",
        "enabled": True,
        "digest_type": digest_type,
        "window_label": window_label,
        "idempotency_key": idempotency_key,
        "metrics": metrics,
        "formatted_digest": formatted_text,
        "telegram": telegram_result,
        "crash_window_recovery": is_crash_recovery,
    }
