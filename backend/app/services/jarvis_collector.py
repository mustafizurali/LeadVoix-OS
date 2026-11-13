"""
LeadVoix Business JARVIS — Read-Only Metrics Collector Service
Phase 1 MVP — Phase A Hardened

Responsibilities:
- Strictly SELECT-only queries against PostgreSQL.
- Strict tenant isolation: filters exclusively on internal organization_id.
- CallProcessingJob scoped by joining AgentCall with internal organization_id filter.
- Mandatory read-only credentials (JARVIS_DATABASE_URL) in production.
- Session-level and transaction-level write prevention guards (commit, flush, add, delete, write SQL).
- Asia/Kolkata timezone window resolution (08:00 morning briefing, 21:00 evening debrief).
- Aggregates Lead generation, Agent Call performance, Deals, Tasks, and System Processing.
- Strict PII minimization: no caller phone numbers, emails, or personal names are exported.
- Zero LLM-generated SQL; uses pure SQLAlchemy parameterized expressions.
"""

from contextlib import contextmanager
from datetime import datetime, time, timedelta, timezone
import logging
import os
from typing import Any, Dict, Generator, Optional, Tuple
from zoneinfo import ZoneInfo

from sqlalchemy import create_engine, func, text
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.config import settings
from backend.app.models.agent_call import AgentCall
from backend.app.models.call_processing_job import CallProcessingJob
from backend.app.models.deal import Deal
from backend.app.models.lead import Lead
from backend.app.models.organization import Organization
from backend.app.models.task import Task


logger = logging.getLogger("leadvoix.jarvis.collector")

DEFAULT_TIMEZONE_NAME = "Asia/Kolkata"
KOLKATA_TZ = ZoneInfo("Asia/Kolkata")
DEFAULT_INTERNAL_ORG_ID = 1


class InvalidTimezoneConfigurationError(ValueError):
    """Raised when JARVIS_TIMEZONE is misconfigured or cannot be resolved."""
    pass


def get_jarvis_timezone(tz_name: Optional[str] = None) -> ZoneInfo:
    """
    Returns the configured ZoneInfo object for JARVIS operations.
    Reads from JARVIS_TIMEZONE env var if tz_name is None, defaulting to Asia/Kolkata.
    Fails closed by raising InvalidTimezoneConfigurationError if the timezone key is invalid.
    """
    raw_tz = tz_name if tz_name is not None else os.getenv("JARVIS_TIMEZONE", DEFAULT_TIMEZONE_NAME)
    if not raw_tz or not raw_tz.strip():
        raw_tz = DEFAULT_TIMEZONE_NAME
    raw_tz = raw_tz.strip()
    try:
        return ZoneInfo(raw_tz)
    except Exception as exc:
        raise InvalidTimezoneConfigurationError(
            f"Invalid JARVIS_TIMEZONE configuration '{raw_tz}': {exc}. Refusing to proceed with invalid timezone."
        ) from exc

# Optional dedicated read-only database engine
_READ_ONLY_ENGINE = None
_READ_ONLY_SESSIONMAKER = None

FORBIDDEN_SQL_VERBS = (
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "TRUNCATE",
    "CREATE",
    "REPLACE",
    "GRANT",
    "REVOKE",
)


class ReadOnlyWriteAttemptError(RuntimeError):
    """Raised if any write, flush, or DML/DDL operation is attempted on a JARVIS read-only session."""
    pass


class CustomerDataWriteViolationError(RuntimeError):
    """Raised if JARVIS operational worker or code attempts to modify customer SaaS tables."""
    pass


CUSTOMER_SAAS_TABLES = (
    "LEADS",
    "AGENT_CALLS",
    "ORGANIZATIONS",
    "DEALS",
    "TASKS",
    "USERS",
    "COMPANIES",
    "CONTACTS",
    "PIPELINES",
    "PIPELINE_STAGES",
    "CALL_PROCESSING_JOBS",
    "AGENT_CALL_TRANSCRIPTS",
    "AGENT_CALL_SUMMARIES",
    "AGENT_CALL_INTELLIGENCE",
    "FOLLOW_UP_TASKS",
    "SUBSCRIPTIONS",
)


def is_production_mode() -> bool:
    """Returns True if the runtime environment is identified as production."""
    env = os.getenv("ENVIRONMENT") or os.getenv("ENV") or os.getenv("NODE_ENV") or ""
    return env.strip().lower() in ("production", "prod")


def is_readonly_db_required() -> bool:
    """Returns True if dedicated read-only credentials must be strictly enforced."""
    if os.getenv("REQUIRE_JARVIS_READONLY", "").strip().lower() in ("true", "1", "yes", "on"):
        return True
    return is_production_mode()


def get_jarvis_database_url() -> str:
    """
    Returns the dedicated read-only database URL.
    In production mode or when REQUIRE_JARVIS_READONLY=true, JARVIS_DATABASE_URL is mandatory.
    Fallback to primary DATABASE_URL is strictly blocked in production to prevent write exposure.
    """
    custom_url = os.getenv("JARVIS_DATABASE_URL")
    if custom_url and custom_url.strip():
        return custom_url.strip()

    if is_readonly_db_required():
        raise RuntimeError(
            "Security violation: JARVIS_DATABASE_URL is mandatory in production mode or when "
            "REQUIRE_JARVIS_READONLY=true. Refusing to connect with default write-enabled credentials."
        )

    return settings.DATABASE_URL


def reset_read_only_engine() -> None:
    """Resets cached read-only engine and sessionmaker (used for test isolation)."""
    global _READ_ONLY_ENGINE, _READ_ONLY_SESSIONMAKER
    if _READ_ONLY_ENGINE is not None:
        try:
            _READ_ONLY_ENGINE.dispose()
        except Exception:
            pass
    _READ_ONLY_ENGINE = None
    _READ_ONLY_SESSIONMAKER = None


def get_internal_org_id() -> int:
    """Returns the verified internal LeadVoix organization ID."""
    raw = os.getenv("JARVIS_INTERNAL_ORG_ID")
    if raw and raw.strip().isdigit():
        return int(raw.strip())
    return DEFAULT_INTERNAL_ORG_ID


def get_read_only_sessionmaker() -> sessionmaker:
    """Lazily initializes and returns a sessionmaker configured for read-only access."""
    global _READ_ONLY_ENGINE, _READ_ONLY_SESSIONMAKER
    if _READ_ONLY_SESSIONMAKER is None:
        db_url = get_jarvis_database_url()
        _READ_ONLY_ENGINE = create_engine(
            db_url,
            pool_pre_ping=True,
            execution_options={"isolation_level": "AUTOCOMMIT"},
        )
        _READ_ONLY_SESSIONMAKER = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=_READ_ONLY_ENGINE,
        )
    return _READ_ONLY_SESSIONMAKER


def _is_write_statement(stmt: Any) -> bool:
    """Checks whether a statement or SQL expression is a write (DML/DDL) operation."""
    visit_name = getattr(stmt, "__visit_name__", "").lower()
    if visit_name in ("insert", "update", "delete"):
        return True

    stmt_str = str(stmt).strip().upper()
    while stmt_str.startswith("--") or stmt_str.startswith("/*"):
        if stmt_str.startswith("--"):
            newline_idx = stmt_str.find("\n")
            stmt_str = stmt_str[newline_idx + 1:].strip() if newline_idx != -1 else ""
        elif stmt_str.startswith("/*"):
            comment_end = stmt_str.find("*/")
            stmt_str = stmt_str[comment_end + 2:].strip() if comment_end != -1 else ""

    if stmt_str.startswith("SET TRANSACTION READ ONLY") or stmt_str.startswith("SET SESSION CHARACTERISTICS"):
        return False

    first_word = stmt_str.split()[0] if stmt_str.split() else ""
    first_word = first_word.lstrip("(")
    return first_word in FORBIDDEN_SQL_VERBS


def apply_read_only_guards(session: Session) -> Session:
    """
    Applies comprehensive in-process write guards to a SQLAlchemy Session.
    Blocks commit, flush, add, add_all, delete, and write SQL execution.
    """
    def _forbidden_write(*args: Any, **kwargs: Any) -> None:
        raise ReadOnlyWriteAttemptError(
            "JARVIS database session is strictly read-only. Data modifications are forbidden."
        )

    session.commit = _forbidden_write  # type: ignore[assignment]
    session.flush = _forbidden_write  # type: ignore[assignment]
    session.add = _forbidden_write  # type: ignore[assignment]
    session.add_all = _forbidden_write  # type: ignore[assignment]
    session.delete = _forbidden_write  # type: ignore[assignment]

    orig_execute = session.execute

    def _guarded_execute(statement: Any, *args: Any, **kwargs: Any) -> Any:
        if _is_write_statement(statement):
            raise ReadOnlyWriteAttemptError(
                f"Write operation forbidden on JARVIS read-only session: {str(statement)[:60]}"
            )
        return orig_execute(statement, *args, **kwargs)

    session.execute = _guarded_execute  # type: ignore[assignment]
    return session


@contextmanager
def get_jarvis_read_only_session(custom_session: Optional[Session] = None) -> Generator[Session, None, None]:
    """
    Context manager yielding a read-only SQLAlchemy Session.
    Enforces SELECT-only queries by applying session-level write guards and setting transaction read-only.
    """
    if custom_session is not None:
        yield apply_read_only_guards(custom_session)
        return

    sm = get_read_only_sessionmaker()
    session = sm()
    session = apply_read_only_guards(session)

    try:
        try:
            session.execute(text("SET TRANSACTION READ ONLY;"))
        except Exception:
            # Fallback for dialects like SQLite that do not support SET TRANSACTION
            pass
        yield session
    finally:
        session.close()


def get_jarvis_read_only_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency yielding a guarded read-only SQLAlchemy session.
    Guarantees endpoints cannot perform write operations.
    """
    with get_jarvis_read_only_session() as session:
        yield session


_OPERATIONAL_ENGINE = None
_OPERATIONAL_SESSIONMAKER = None


def is_operational_db_required() -> bool:
    """Returns True if dedicated operational credentials must be strictly enforced."""
    if os.getenv("REQUIRE_JARVIS_OPERATIONAL", "").strip().lower() in ("true", "1", "yes", "on"):
        return True
    return is_production_mode()


def get_jarvis_operational_database_url() -> str:
    """
    Returns the dedicated operational database URL.
    In production mode or when REQUIRE_JARVIS_OPERATIONAL=true, JARVIS_OPERATIONAL_DATABASE_URL is mandatory.
    Silent fallback to primary DATABASE_URL is strictly blocked to prevent unauthorized superuser access.
    """
    custom_url = os.getenv("JARVIS_OPERATIONAL_DATABASE_URL")
    if custom_url and custom_url.strip():
        return custom_url.strip()

    if is_operational_db_required():
        raise RuntimeError(
            "Security violation: JARVIS_OPERATIONAL_DATABASE_URL is mandatory in production mode or when "
            "REQUIRE_JARVIS_OPERATIONAL=true. Refusing to connect with primary superuser credentials."
        )

    return settings.DATABASE_URL


def reset_operational_engine() -> None:
    """Resets cached operational engine and sessionmaker (used for test isolation)."""
    global _OPERATIONAL_ENGINE, _OPERATIONAL_SESSIONMAKER
    if _OPERATIONAL_ENGINE is not None:
        try:
            _OPERATIONAL_ENGINE.dispose()
        except Exception:
            pass
    _OPERATIONAL_ENGINE = None
    _OPERATIONAL_SESSIONMAKER = None


def get_operational_sessionmaker() -> sessionmaker:
    """Lazily initializes and returns an operational sessionmaker with bounded pooling and standard transactions."""
    global _OPERATIONAL_ENGINE, _OPERATIONAL_SESSIONMAKER
    if _OPERATIONAL_SESSIONMAKER is None:
        db_url = get_jarvis_operational_database_url()
        # Bounded pooling & standard READ COMMITTED transactions (no AUTOCOMMIT)
        engine_kwargs: dict[str, Any] = {
            "pool_pre_ping": True,
        }
        if "sqlite" not in db_url.lower():
            engine_kwargs.update({
                "pool_size": 3,
                "max_overflow": 2,
                "pool_timeout": 30,
                "pool_recycle": 1800,
            })
        _OPERATIONAL_ENGINE = create_engine(
            db_url,
            **engine_kwargs,
        )
        _OPERATIONAL_SESSIONMAKER = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=_OPERATIONAL_ENGINE,
        )
    return _OPERATIONAL_SESSIONMAKER


def apply_operational_guards(session: Session) -> Session:
    """
    Applies boundary protection to an operational SQLAlchemy Session.
    Operational writes to jarvis.* schema tables are permitted.
    Writes, updates, or deletes touching customer SaaS tables in public schema are strictly blocked.
    """
    orig_execute = session.execute
    orig_add = session.add
    orig_add_all = session.add_all
    orig_delete = session.delete

    def _check_saas_entity(instance: Any) -> None:
        table_name = getattr(getattr(instance, "__table__", None), "name", "").upper()
        schema_name = getattr(getattr(instance, "__table__", None), "schema", "")
        if schema_name != "jarvis" and table_name in CUSTOMER_SAAS_TABLES:
            raise CustomerDataWriteViolationError(
                f"Operational boundary violation: writes to customer SaaS table '{table_name}' are forbidden."
            )

    def _guarded_add(instance: Any, _warn: bool = True) -> None:
        _check_saas_entity(instance)
        return orig_add(instance, _warn=_warn)

    def _guarded_add_all(instances: Any) -> None:
        for inst in instances:
            _check_saas_entity(inst)
        return orig_add_all(instances)

    def _guarded_delete(instance: Any) -> None:
        _check_saas_entity(instance)
        return orig_delete(instance)

    def _guarded_execute(statement: Any, *args: Any, **kwargs: Any) -> Any:
        if _is_write_statement(statement):
            stmt_upper = str(statement).upper()
            for saas_tbl in CUSTOMER_SAAS_TABLES:
                if saas_tbl in stmt_upper and f"JARVIS.{saas_tbl}" not in stmt_upper:
                    raise CustomerDataWriteViolationError(
                        f"Operational boundary violation: SQL write touching customer SaaS table '{saas_tbl}' is forbidden."
                    )
        return orig_execute(statement, *args, **kwargs)

    session.add = _guarded_add  # type: ignore[assignment]
    session.add_all = _guarded_add_all  # type: ignore[assignment]
    session.delete = _guarded_delete  # type: ignore[assignment]
    session.execute = _guarded_execute  # type: ignore[assignment]
    return session


@contextmanager
def get_jarvis_operational_session(custom_session: Optional[Session] = None) -> Generator[Session, None, None]:
    """
    Context manager yielding an operational SQLAlchemy Session.
    Guarded to allow writes in jarvis.* while blocking modifications on customer SaaS data.
    """
    if custom_session is not None:
        yield apply_operational_guards(custom_session)
        return

    sm = get_operational_sessionmaker()
    session = sm()
    session = apply_operational_guards(session)
    try:
        yield session
    finally:
        session.close()


def get_jarvis_operational_db() -> Generator[Session, None, None]:
    """FastAPI generator dependency yielding an operational SQLAlchemy session."""
    with get_jarvis_operational_session() as session:
        yield session


def calculate_digest_window(
    digest_type: str,
    target_date: Optional[datetime.date] = None,
    tz: Optional[ZoneInfo] = None,
) -> Tuple[datetime, datetime, str]:
    """
    Calculates the start and end timestamps (and UTC equivalents) for a given digest type,
    grounded in the configured JARVIS_TIMEZONE (default Asia/Kolkata).

    - 'morning' (08:00 local briefing):
      Summarizes the previous full day (00:00:00 to 23:59:59.999999 local).
    - 'evening' (21:00 local debrief):
      Summarizes today from start of day up to 21:00:00 local.
    - 'custom' or other:
      Defaults to the past 24 hours.

    Returns:
        (start_time_utc, end_time_utc, label_local)
    """
    resolved_tz = tz or get_jarvis_timezone()
    now_local = datetime.now(resolved_tz)
    ref_date = target_date or now_local.date()
    tz_key = getattr(resolved_tz, "key", str(resolved_tz))
    tz_abbr = "IST" if tz_key == "Asia/Kolkata" else tz_key

    if digest_type == "morning":
        # Previous full day
        prev_date = ref_date - timedelta(days=1)
        start_local = datetime.combine(prev_date, time.min, tzinfo=resolved_tz)
        end_local = datetime.combine(prev_date, time.max, tzinfo=resolved_tz)
        label = f"Morning Briefing — Activity for {prev_date.strftime('%d-%b-%Y')}"
    elif digest_type == "evening":
        # Today up to 21:00
        start_local = datetime.combine(ref_date, time.min, tzinfo=resolved_tz)
        end_local = datetime.combine(ref_date, time(21, 0, 0), tzinfo=resolved_tz)
        label = f"Evening Debrief — Activity for {ref_date.strftime('%d-%b-%Y')} (00:00 - 21:00 {tz_abbr})"
    else:
        # Rolling 24-hour window
        end_local = now_local
        start_local = end_local - timedelta(hours=24)
        label = f"Rolling 24-Hour Summary ({start_local.strftime('%d-%b %H:%M')} to {end_local.strftime('%d-%b %H:%M')} {tz_abbr})"

    start_utc = start_local.astimezone(timezone.utc)
    end_utc = end_local.astimezone(timezone.utc)

    return start_utc, end_utc, label


def collect_jarvis_metrics(
    db: Session,
    org_id: Optional[int] = None,
    start_utc: Optional[datetime] = None,
    end_utc: Optional[datetime] = None,
) -> Dict[str, Any]:
    """
    Executes SELECT-only aggregations for the internal organization.
    Collects counts, durations, status distributions, and pipeline stats without exposing PII.
    Tenant isolation:
    - Filters Organization, Lead, AgentCall, Deal, Task by organization_id == internal_org_id.
    - Joins CallProcessingJob on AgentCall and filters AgentCall.organization_id == internal_org_id.
    """
    internal_org_id = org_id or get_internal_org_id()

    # Default to last 24 hours if window not provided
    if end_utc is None:
        end_utc = datetime.now(timezone.utc)
    if start_utc is None:
        start_utc = end_utc - timedelta(hours=24)

    # 1. Organization verification
    org = (
        db.query(Organization.id, Organization.name, Organization.slug, Organization.plan)
        .filter(Organization.id == internal_org_id)
        .first()
    )

    org_info = {
        "id": internal_org_id,
        "name": org.name if org else f"Organization #{internal_org_id}",
        "slug": org.slug if org else "unknown",
        "plan": org.plan if org else "unknown",
    }

    # 2. Leads Metrics
    total_leads_query = (
        db.query(func.count(Lead.id))
        .filter(
            Lead.organization_id == internal_org_id,
            Lead.created_at >= start_utc,
            Lead.created_at <= end_utc,
        )
        .scalar()
        or 0
    )

    leads_by_status = dict(
        db.query(Lead.status, func.count(Lead.id))
        .filter(
            Lead.organization_id == internal_org_id,
            Lead.created_at >= start_utc,
            Lead.created_at <= end_utc,
        )
        .group_by(Lead.status)
        .all()
    )

    leads_by_source = dict(
        db.query(Lead.source, func.count(Lead.id))
        .filter(
            Lead.organization_id == internal_org_id,
            Lead.created_at >= start_utc,
            Lead.created_at <= end_utc,
        )
        .group_by(Lead.source)
        .all()
    )

    # 3. Agent Calls Metrics
    calls_query = (
        db.query(
            func.count(AgentCall.id).label("total_calls"),
            func.coalesce(func.sum(AgentCall.duration), 0).label("total_duration_sec"),
            func.coalesce(func.avg(AgentCall.duration), 0).label("avg_duration_sec"),
        )
        .filter(
            AgentCall.organization_id == internal_org_id,
            AgentCall.created_at >= start_utc,
            AgentCall.created_at <= end_utc,
        )
        .first()
    )

    total_calls = calls_query.total_calls if calls_query else 0
    total_duration_sec = int(calls_query.total_duration_sec if calls_query else 0)
    avg_duration_sec = round(float(calls_query.avg_duration_sec if calls_query else 0), 1)

    calls_by_status = dict(
        db.query(AgentCall.status, func.count(AgentCall.id))
        .filter(
            AgentCall.organization_id == internal_org_id,
            AgentCall.created_at >= start_utc,
            AgentCall.created_at <= end_utc,
        )
        .group_by(AgentCall.status)
        .all()
    )

    calls_by_direction = dict(
        db.query(AgentCall.direction, func.count(AgentCall.id))
        .filter(
            AgentCall.organization_id == internal_org_id,
            AgentCall.created_at >= start_utc,
            AgentCall.created_at <= end_utc,
        )
        .group_by(AgentCall.direction)
        .all()
    )

    # 4. Deals Metrics
    total_deals = (
        db.query(func.count(Deal.id))
        .filter(
            Deal.organization_id == internal_org_id,
            Deal.created_at >= start_utc,
            Deal.created_at <= end_utc,
        )
        .scalar()
        or 0
    )

    deals_by_status = dict(
        db.query(Deal.status, func.count(Deal.id))
        .filter(
            Deal.organization_id == internal_org_id,
            Deal.created_at >= start_utc,
            Deal.created_at <= end_utc,
        )
        .group_by(Deal.status)
        .all()
    )

    won_deals_val = (
        db.query(func.coalesce(func.sum(Deal.amount), 0))
        .filter(
            Deal.organization_id == internal_org_id,
            Deal.status == "WON",
            Deal.created_at >= start_utc,
            Deal.created_at <= end_utc,
        )
        .scalar()
        or 0
    )

    # 5. Tasks Metrics
    tasks_summary = dict(
        db.query(Task.status, func.count(Task.id))
        .filter(
            Task.organization_id == internal_org_id,
            Task.created_at >= start_utc,
            Task.created_at <= end_utc,
        )
        .group_by(Task.status)
        .all()
    )

    # 6. Call Processing Background Jobs (Strict Tenant Isolation via AgentCall join)
    jobs_summary = dict(
        db.query(CallProcessingJob.status, func.count(CallProcessingJob.id))
        .join(AgentCall, CallProcessingJob.agent_call_id == AgentCall.id)
        .filter(
            AgentCall.organization_id == internal_org_id,
            CallProcessingJob.created_at >= start_utc,
            CallProcessingJob.created_at <= end_utc,
        )
        .group_by(CallProcessingJob.status)
        .all()
    )

    active_tz = get_jarvis_timezone()
    tz_key = getattr(active_tz, "key", str(active_tz))
    tz_abbr = "IST" if tz_key == "Asia/Kolkata" else tz_key

    return {
        "organization": org_info,
        "window": {
            "start_utc": start_utc.isoformat(),
            "end_utc": end_utc.isoformat(),
            "start_kolkata": start_utc.astimezone(KOLKATA_TZ).strftime("%Y-%m-%d %H:%M:%S IST"),
            "end_kolkata": end_utc.astimezone(KOLKATA_TZ).strftime("%Y-%m-%d %H:%M:%S IST"),
            "start_local": start_utc.astimezone(active_tz).strftime(f"%Y-%m-%d %H:%M:%S {tz_abbr}"),
            "end_local": end_utc.astimezone(active_tz).strftime(f"%Y-%m-%d %H:%M:%S {tz_abbr}"),
            "timezone": tz_key,
        },
        "telephony": {
            "total_calls": total_calls,
            "total_duration_seconds": total_duration_sec,
            "total_duration_minutes": round(total_duration_sec / 60.0, 1),
            "average_duration_seconds": avg_duration_sec,
            "status_breakdown": calls_by_status,
            "direction_breakdown": calls_by_direction,
        },
        "leads": {
            "total_leads": total_leads_query,
            "status_breakdown": leads_by_status,
            "source_breakdown": leads_by_source,
        },
        "deals": {
            "total_deals_created": total_deals,
            "status_breakdown": deals_by_status,
            "won_amount_total": float(won_deals_val),
        },
        "tasks": {
            "status_breakdown": tasks_summary,
        },
        "system_jobs": {
            "processing_jobs_summary": jobs_summary,
        },
    }
