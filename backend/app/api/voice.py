import asyncio
import logging
import os
import re
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse

from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, Request, status
from fastapi.responses import Response
from sqlalchemy import func
from sqlalchemy.orm import Session
from twilio.request_validator import RequestValidator
from twilio.twiml.voice_response import VoiceResponse, Gather

from backend.app.core.config import settings
from backend.app.db.database import get_db, SessionLocal
from backend.app.models.agent import Agent
from backend.app.models.agent_call import AgentCall
from backend.app.models.agent_call_intelligence import AgentCallIntelligence
from backend.app.models.agent_call_transcript import AgentCallTranscript
from backend.app.models.call_processing_job import CallProcessingJob
from backend.app.services.agent_call_transcript import get_agent_call_transcripts
from backend.app.services.call_processing_worker import (
    run_worker_cycle,
)
from backend.app.services.ai_voice_conversation import (
    generate_ai_voice_response,
    EMPTY_INPUT_RESPONSE,
    FALLBACK_RESPONSE,
)


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/voice/twilio",
    tags=["Twilio Voice"],
)

SUPPORTED_STATUSES = {
    "initiated",
    "ringing",
    "in-progress",
    "completed",
    "busy",
    "no-answer",
    "failed",
    "canceled",
}
TERMINAL_STATUSES = {"completed", "busy", "no-answer", "failed", "canceled"}

MAX_CONVERSATION_TURNS = int(os.getenv("MAX_CONVERSATION_TURNS", "10"))

GOODBYE_PATTERNS = [
    r"\b(good\s*bye|bye\s*bye|bye)\b",
    r"\b(farewell|see\s+ya|see\s+you|talk\s+to\s+you\s+later)\b",
    r"\b(end\s+call|hang\s*up)\b",
    r"\b(that'?s\s+all|nothing\s+else|no\s+thanks,?\s+bye)\b",
]

SUPPORTED_TWILIO_GATHER_LANGUAGES = {
    "en-US", "en-GB", "en-AU", "en-IN", "en-NZ", "en-CA",
    "es-ES", "es-US", "es-MX",
    "fr-FR", "fr-CA",
    "de-DE",
    "it-IT",
    "pt-BR", "pt-PT",
}


def resolve_gather_language(lang: Optional[str]) -> str:
    if not lang or not isinstance(lang, str):
        return "en-US"
    clean_lang = lang.strip()
    if clean_lang in SUPPORTED_TWILIO_GATHER_LANGUAGES:
        return clean_lang
    if clean_lang.lower() == "en":
        return "en-US"
    return "en-US"


def is_goodbye_intent(text: str) -> bool:
    if not text:
        return False
    clean = text.strip().lower()
    for pat in GOODBYE_PATTERNS:
        if re.search(pat, clean):
            return True
    return False


def _generate_ai_response_in_worker(
    agent_id: int,
    call_id: int,
    user_speech: str,
) -> str:
    """Safely executes AI voice generation in a separate thread using a dedicated worker Session."""
    worker_db = SessionLocal()
    try:
        worker_agent = worker_db.query(Agent).filter(Agent.id == agent_id).first()
        if not worker_agent:
            logger.warning("Worker thread: Agent %s not found", agent_id)
            return FALLBACK_RESPONSE

        worker_call = worker_db.query(AgentCall).filter(AgentCall.id == call_id).first()
        if not worker_call:
            logger.warning("Worker thread: AgentCall %s not found", call_id)
            return FALLBACK_RESPONSE

        if worker_call.agent_id != worker_agent.id:
            logger.warning(
                "Worker thread: AgentCall %s does not belong to Agent %s",
                call_id,
                agent_id,
            )
            return FALLBACK_RESPONSE

        if worker_call.organization_id != worker_agent.organization_id:
            logger.warning(
                "Worker thread: Organization mismatch for AgentCall %s and Agent %s",
                call_id,
                agent_id,
            )
            return FALLBACK_RESPONSE

        return generate_ai_voice_response(
            db=worker_db,
            agent=worker_agent,
            agent_call=worker_call,
            user_speech=user_speech,
        )
    except Exception as exc:
        logger.error("Worker thread error during AI response generation: %s", exc)
        return FALLBACK_RESPONSE
    finally:
        worker_db.close()


def normalize_call_status(twilio_status: str) -> Optional[str]:
    s = (twilio_status or "").strip().lower()
    if s in ("answered", "in-progress", "in_progress"):
        s = "in-progress"
    elif s in ("no-answer", "no_answer"):
        s = "no-answer"
    if s in SUPPORTED_STATUSES:
        return s
    return None


def is_valid_recording_url(url: Optional[str]) -> bool:
    if not url or not isinstance(url, str):
        return False
    try:
        parsed = urlparse(url.strip())
        if parsed.scheme not in ("http", "https"):
            return False
        if not parsed.hostname:
            return False
        # Accessing parsed.port validates port and raises ValueError if malformed
        _ = parsed.port
        return True
    except Exception:
        return False


def enqueue_job_on_conflict_do_nothing(db: Session, agent_call_id: int) -> bool:
    """
    Atomically enqueues a CallProcessingJob using PostgreSQL ON CONFLICT DO NOTHING.
    Fallback to SQLite dialect for local test suites.
    Does NOT commit the session.
    """
    dialect_name = "postgresql"
    try:
        bind = db.get_bind() if hasattr(db, "get_bind") else getattr(db, "bind", None)
        if bind and hasattr(bind, "dialect") and hasattr(bind.dialect, "name"):
            dialect_name = bind.dialect.name
    except Exception:
        dialect_name = "postgresql"

    if dialect_name == "sqlite":
        from sqlalchemy.dialects.sqlite import insert as sqlite_insert

        stmt = (
            sqlite_insert(CallProcessingJob)
            .values(
                agent_call_id=agent_call_id,
                job_type="call_intelligence",
                status="pending",
            )
            .on_conflict_do_nothing()
        )
    else:
        from sqlalchemy.dialects.postgresql import insert as pg_insert

        stmt = (
            pg_insert(CallProcessingJob)
            .values(
                agent_call_id=agent_call_id,
                job_type="call_intelligence",
                status="pending",
            )
            .on_conflict_do_nothing(
                constraint="uq_call_processing_jobs_agent_call_id"
            )
        )

    res = db.execute(stmt)
    rowcount = getattr(res, "rowcount", None)
    if isinstance(rowcount, int):
        return rowcount > 0
    return True


def try_enqueue_call_processing_job(db: Session, agent_call: AgentCall) -> bool:
    """
    Evaluates post-call intelligence eligibility and atomically enqueues a
    CallProcessingJob if eligible:
    1. agent_call.status == 'completed'
    2. Non-empty transcript exists (in agent_call.transcript or AgentCallTranscript)
    3. No AgentCallIntelligence record exists yet

    Returns True if an enqueue statement was executed, False otherwise.
    Does NOT commit the session.
    """
    if not agent_call or agent_call.status != "completed":
        return False

    has_transcript = bool(agent_call.transcript and agent_call.transcript.strip())
    if not has_transcript:
        has_transcript = (
            db.query(AgentCallTranscript)
            .filter(
                AgentCallTranscript.agent_call_id == agent_call.id,
                AgentCallTranscript.message.isnot(None),
                AgentCallTranscript.message != "",
                func.trim(AgentCallTranscript.message) != "",
            )
            .first()
            is not None
        )

    if not has_transcript:
        return False

    already_analyzed = (
        db.query(AgentCallIntelligence)
        .filter(AgentCallIntelligence.agent_call_id == agent_call.id)
        .first()
        is not None
    )

    if already_analyzed:
        return False

    return enqueue_job_on_conflict_do_nothing(db, agent_call.id)


TRUSTED_DEV_HOSTS = {"localhost", "127.0.0.1", "testserver"}
TRUSTED_NGROK_REGEX = re.compile(
    r"^[a-zA-Z0-9\-]+\.(ngrok\-free\.app|ngrok\.io|ngrok\.app)$",
    re.IGNORECASE,
)


def get_trusted_hosts() -> set[str]:
    """Returns the set of explicitly configured trusted hostnames (lowercased, without port)."""
    trusted = set(TRUSTED_DEV_HOSTS)
    if settings.BACKEND_BASE_URL:
        try:
            parsed = urlparse(settings.BACKEND_BASE_URL)
            if parsed.hostname:
                trusted.add(parsed.hostname.lower())
        except Exception:
            pass
    if getattr(settings, "ALLOWED_HOSTS", None):
        for entry in settings.ALLOWED_HOSTS.split(","):
            cleaned = entry.strip().lower()
            if cleaned:
                trusted.add(cleaned)
    return trusted


def is_host_trusted(host: Optional[str]) -> bool:
    """
    Validates whether a host (from Host or X-Forwarded-Host) is trusted.
    Prevents host header injection attacks from spoofed reverse-proxy headers.
    """
    if not host:
        return False
    clean_host = host.split(":")[0].strip().lower()
    if not clean_host:
        return False

    trusted_set = get_trusted_hosts()
    if clean_host in trusted_set:
        return True

    for entry in trusted_set:
        if entry.startswith("*."):
            suffix = entry[1:]
            if clean_host.endswith(suffix) and len(clean_host) > len(suffix):
                return True

    if TRUSTED_NGROK_REGEX.match(clean_host):
        return True

    return False


def reconstruct_public_webhook_urls(request: Request) -> list[str]:
    """
    Reconstructs candidate public webhook URLs in priority order for Twilio validation:
    1. Configured BACKEND_BASE_URL + path + query string.
    2. Forwarded reverse-proxy scheme and host (X-Forwarded-Proto, X-Forwarded-Host)
       ONLY when TRUST_PROXY_HEADERS is True and the host is in the trusted host whitelist.
    3. Direct request host (for local development or test client environments).
    """
    candidates: list[str] = []
    query_suffix = f"?{request.url.query}" if request.url.query else ""
    path = request.url.path

    # Candidate 1: Authoritative public base URL
    base_url = (settings.BACKEND_BASE_URL or "").rstrip("/")
    if base_url:
        candidates.append(f"{base_url}{path}{query_suffix}")

    # Candidate 2: Trusted reverse proxy headers (e.g. Render / ngrok)
    if getattr(settings, "TRUST_PROXY_HEADERS", True):
        fwd_host = request.headers.get("x-forwarded-host")
        if fwd_host:
            first_host = fwd_host.split(",")[0].strip()
            if is_host_trusted(first_host):
                proto = (
                    request.headers.get("x-forwarded-proto") or "https"
                ).split(",")[0].strip().lower()
                if proto not in ("http", "https"):
                    proto = "https"
                proxy_url = f"{proto}://{first_host}{path}{query_suffix}"
                if proxy_url not in candidates:
                    candidates.append(proxy_url)
            else:
                logger.warning(
                    "Rejected untrusted X-Forwarded-Host header: %s",
                    first_host,
                )

    # Candidate 3: Request host if trusted (local dev / testclient)
    req_host = request.headers.get("host") or request.url.netloc
    if req_host:
        first_req_host = req_host.split(",")[0].strip()
        if is_host_trusted(first_req_host):
            proto = request.url.scheme or "http"
            direct_url = f"{proto}://{first_req_host}{path}{query_suffix}"
            if direct_url not in candidates:
                candidates.append(direct_url)

    return candidates


async def verify_twilio_signature(request: Request) -> None:
    signature = request.headers.get("X-Twilio-Signature")
    if not signature:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing or invalid Twilio signature",
        )

    auth_token = settings.TWILIO_AUTH_TOKEN
    if not auth_token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Twilio auth token is not configured",
        )

    validator = RequestValidator(auth_token)

    form_data = await request.form()
    params = dict(form_data)

    candidate_urls = reconstruct_public_webhook_urls(request)
    if not candidate_urls:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No valid candidate webhook URL could be determined",
        )

    is_valid = any(
        validator.validate(candidate_url, params, signature)
        for candidate_url in candidate_urls
    )
    if not is_valid:
        logger.warning(
            "Twilio signature validation failed. Checked candidates: %s",
            candidate_urls,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Twilio signature",
        )


def twiml_response(response: VoiceResponse) -> Response:
    return Response(
        content=str(response),
        media_type="application/xml",
    )


async def resolve_agent_and_call(
    db: Session,
    agent_id: Optional[int],
    call_id: Optional[int],
    call_sid: str = "",
    auto_progress: bool = True,
) -> tuple[Optional[Agent], Optional[AgentCall]]:
    # If neither parameter is provided, return None (backward compatibility for bare probes)
    if agent_id is None and call_id is None:
        return None, None

    if agent_id is None or call_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both agent_id and call_id must be provided in the webhook URL",
        )

    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )

    # Resolve call, retrying briefly for the transaction commit race condition
    agent_call = db.query(AgentCall).filter(AgentCall.id == call_id).first()
    if not agent_call:
        for _ in range(3):
            await asyncio.sleep(0.1)
            db.expire_all()
            agent_call = db.query(AgentCall).filter(AgentCall.id == call_id).first()
            if agent_call:
                break

    if not agent_call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent call not found",
        )

    if agent_call.agent_id != agent.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent call does not match requested agent",
        )

    if agent_call.organization_id != agent.organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization mismatch",
        )

    clean_sid = call_sid.strip() if call_sid else ""
    if clean_sid:
        if not agent_call.provider_call_id:
            agent_call.provider_call_id = clean_sid
        elif agent_call.provider_call_id != clean_sid:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Twilio Call SID does not match recorded call",
            )

    if auto_progress and agent_call.status in ("queued", "initiated"):
        agent_call.status = "in-progress"
        if not agent_call.started_at:
            agent_call.started_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(agent_call)

    return agent, agent_call


@router.post(
    "/answer",
    dependencies=[Depends(verify_twilio_signature)],
)
async def answer_call(
    agent_id: Optional[int] = None,
    call_id: Optional[int] = None,
    call_sid: str = Form("", alias="CallSid"),
    db: Session = Depends(get_db),
):
    agent, agent_call = await resolve_agent_and_call(
        db=db,
        agent_id=agent_id,
        call_id=call_id,
        call_sid=call_sid,
        auto_progress=True,
    )

    base_url = (settings.BACKEND_BASE_URL or "").rstrip("/")
    if agent and agent_call:
        action_url = (
            f"{base_url}/voice/twilio/process?"
            f"agent_id={agent.id}&call_id={agent_call.id}&turn=1"
        )
        greeting = agent.greeting_message or (
            f"Hello. I am {agent.name}. "
            "I am an artificial intelligence voice assistant. "
            "How can I help you today?"
        )
    else:
        action_url = f"{base_url}/voice/twilio/process"
        greeting = (
            "Hello. I am LeadVoix AI. "
            "I am an artificial intelligence voice assistant. "
            "How can I help you today?"
        )

    response = VoiceResponse()

    say_kwargs = {}
    if agent and agent.voice:
        say_kwargs["voice"] = agent.voice

    gather_language = resolve_gather_language(agent.language if agent else None)

    gather = Gather(
        input="speech",
        action=action_url,
        method="POST",
        language=gather_language,
        speech_timeout="auto",
    )

    gather.say(greeting, **say_kwargs)

    response.append(gather)

    response.say(
        "I did not hear anything. Goodbye.",
        **say_kwargs,
    )
    response.hangup()

    return twiml_response(response)


@router.post(
    "/process",
    dependencies=[Depends(verify_twilio_signature)],
)
async def process_speech(
    agent_id: Optional[int] = None,
    call_id: Optional[int] = None,
    turn: Optional[int] = None,
    call_sid: str = Form("", alias="CallSid"),
    speech_result: str = Form("", alias="SpeechResult"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
):
    agent, agent_call = await resolve_agent_and_call(
        db=db,
        agent_id=agent_id,
        call_id=call_id,
        call_sid=call_sid,
        auto_progress=True,
    )

    clean_speech = (speech_result or "").strip()[:1000]

    # Legacy fallback when no agent or call context is present
    if not agent or not agent_call:
        response = VoiceResponse()
        if clean_speech:
            response.say(
                f"You said: {clean_speech}. "
                "Thank you. This is the LeadVoix AI test."
            )
        else:
            response.say(
                "I could not understand you. Goodbye."
            )
        response.hangup()
        return twiml_response(response)

    # Legacy test probe compatibility: if turn is omitted, preserve legacy echo response
    if turn is None:
        response = VoiceResponse()
        if clean_speech:
            agent_name = agent.name if agent else "LeadVoix AI"
            response.say(
                f"You said: {clean_speech}. "
                f"Thank you. This is the {agent_name} test."
            )
        else:
            response.say(
                "I could not understand you. Goodbye."
            )
        response.hangup()
        return twiml_response(response)

    # --- Turn Validation ---
    if turn <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid turn number: must be greater than zero",
        )
    if turn > MAX_CONVERSATION_TURNS + 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Excessive turn number: exceeds maximum allowed threshold of {MAX_CONVERSATION_TURNS + 10}",
        )

    base_url = (settings.BACKEND_BASE_URL or "").rstrip("/")
    say_kwargs = {}
    if agent.voice:
        say_kwargs["voice"] = agent.voice

    gather_language = resolve_gather_language(agent.language if agent else None)

    # If the configured maximum turn limit has already been exceeded, do not invoke AI generation
    if turn > MAX_CONVERSATION_TURNS:
        response = VoiceResponse()
        response.say("Thank you for calling. This conversation has concluded. Goodbye.", **say_kwargs)
        response.hangup()
        return twiml_response(response)

    current_turn = turn

    # Empty speech handling: re-prompt caller without saving empty transcripts
    if not clean_speech:
        response = VoiceResponse()
        action_url = (
            f"{base_url}/voice/twilio/process?"
            f"agent_id={agent.id}&call_id={agent_call.id}&turn={current_turn}"
        )
        gather = Gather(
            input="speech",
            action=action_url,
            method="POST",
            language=gather_language,
            speech_timeout="auto",
        )
        gather.say(EMPTY_INPUT_RESPONSE, **say_kwargs)
        response.append(gather)
        response.say("I did not hear anything. Goodbye.", **say_kwargs)
        response.hangup()
        return twiml_response(response)

    # --- Row-level Serialization & Lock ---
    try:
        locked_agent_call = (
            db.query(AgentCall)
            .filter(AgentCall.id == agent_call.id)
            .with_for_update()
            .first()
        )
    except Exception as exc:
        db.rollback()
        logger.error(
            "Failed to acquire row lock for call_id=%s on turn=%s: %s",
            agent_call.id,
            current_turn,
            type(exc).__name__,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database lock acquisition failed",
        )

    if not locked_agent_call:
        db.rollback()
        logger.warning(
            "AgentCall %s no longer found while acquiring row lock on turn=%s",
            agent_call.id,
            current_turn,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent call not found",
        )

    agent_call = locked_agent_call

    # Retrieve existing transcripts under row lock
    existing_transcripts = (
        db.query(AgentCallTranscript)
        .filter(AgentCallTranscript.agent_call_id == agent_call.id)
        .order_by(AgentCallTranscript.id.asc())
        .all()
    )

    user_transcripts = [
        t
        for t in existing_transcripts
        if (t.speaker or "").strip().lower() in ("user", "caller", "customer", "lead")
    ]

    # If the conversation history already has MAX_CONVERSATION_TURNS, check for valid retry
    if len(user_transcripts) >= MAX_CONVERSATION_TURNS:
        # If it's not a retry of that exact last turn, do not generate AI response
        if turn == len(user_transcripts) and (user_transcripts[-1].message or "").strip() == clean_speech:
            pass
        else:
            response = VoiceResponse()
            response.say("Thank you for calling. This conversation has concluded. Goodbye.", **say_kwargs)
            response.hangup()
            return twiml_response(response)

    ai_reply: Optional[str] = None
    is_retry = False

    # Check for webhook retry idempotency and conflicting speech
    if len(user_transcripts) >= turn:
        target_user_t = user_transcripts[turn - 1]
        target_msg = (target_user_t.message or "").strip()
        if target_msg == clean_speech:
            for t in existing_transcripts:
                if t.id > target_user_t.id and (t.speaker or "").strip().lower() in ("agent", "assistant"):
                    ai_reply = t.message
                    is_retry = True
                    break
        else:
            logger.warning(
                "Conflicting speech input for already processed turn %s on call %s",
                turn,
                agent_call.id,
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Turn {turn} has already been processed with different speech input",
            )

    # If new turn, generate response via worker thread using worker-owned session
    if not is_retry:
        ai_reply = await asyncio.to_thread(
            _generate_ai_response_in_worker,
            agent.id,
            agent_call.id,
            clean_speech,
        )

        user_record = AgentCallTranscript(
            agent_call_id=agent_call.id,
            speaker="user",
            message=clean_speech,
        )
        agent_record = AgentCallTranscript(
            agent_call_id=agent_call.id,
            speaker="agent",
            message=ai_reply,
        )
        db.add(user_record)
        db.add(agent_record)

        call_turn_text = f"Customer: {clean_speech}\nAgent: {ai_reply}"
        if agent_call.transcript and agent_call.transcript.strip():
            agent_call.transcript = f"{agent_call.transcript.strip()}\n\n{call_turn_text}"
        else:
            agent_call.transcript = call_turn_text

        db.commit()
        db.refresh(agent_call)

        # If call was already marked completed by an earlier status-callback,
        # enqueue the processing job now that transcripts are committed.
        if agent_call.status == "completed":
            if try_enqueue_call_processing_job(db, agent_call):
                db.commit()
                if background_tasks is not None:
                    background_tasks.add_task(
                        run_worker_cycle,
                        worker_id=f"voice-process-{agent_call.id}",
                    )

    # Deterministic conversation termination: goodbye intent or maximum turns reached
    is_goodbye = is_goodbye_intent(clean_speech) or is_goodbye_intent(ai_reply or "")
    is_max_turns = current_turn >= MAX_CONVERSATION_TURNS

    response = VoiceResponse()

    if is_goodbye or is_max_turns:
        if ai_reply:
            response.say(ai_reply, **say_kwargs)
        if is_max_turns and not is_goodbye:
            response.say("Thank you for calling. Goodbye.", **say_kwargs)
        response.hangup()
        return twiml_response(response)

    # Multi-turn continuation: Return Gather with next turn
    next_turn = current_turn + 1
    action_url = (
        f"{base_url}/voice/twilio/process?"
        f"agent_id={agent.id}&call_id={agent_call.id}&turn={next_turn}"
    )
    gather = Gather(
        input="speech",
        action=action_url,
        method="POST",
        language=gather_language,
        speech_timeout="auto",
    )
    gather.say(ai_reply or "", **say_kwargs)
    response.append(gather)

    response.say("I did not hear anything. Goodbye.", **say_kwargs)
    response.hangup()

    return twiml_response(response)


@router.post(
    "/status-callback",
    dependencies=[Depends(verify_twilio_signature)],
)
async def call_status_callback(
    background_tasks: BackgroundTasks,
    agent_id: Optional[int] = None,
    call_id: Optional[int] = None,
    call_sid: str = Form("", alias="CallSid"),
    call_status: str = Form("", alias="CallStatus"),
    call_duration: Optional[str] = Form(None, alias="CallDuration"),
    recording_url: Optional[str] = Form(None, alias="RecordingUrl"),
    db: Session = Depends(get_db),
):
    normalized_status = normalize_call_status(call_status if isinstance(call_status, str) else "")
    if not normalized_status:
        logger.warning(
            "Ignored unsupported callback status '%s' for call_id=%s, agent_id=%s",
            call_status,
            call_id,
            agent_id,
        )
        return {
            "status": "ignored",
            "call_id": call_id,
            "call_status": None,
            "detail": f"Unsupported or empty callback status '{call_status}'",
        }

    agent, agent_call = await resolve_agent_and_call(
        db=db,
        agent_id=agent_id,
        call_id=call_id,
        call_sid=call_sid,
        auto_progress=False,
    )

    if not agent or not agent_call:
        return {"status": "ignored", "detail": "No agent or call context"}

    is_already_terminal = agent_call.status in TERMINAL_STATUSES
    is_new_status_terminal = normalized_status in TERMINAL_STATUSES

    # Prevent stale callbacks from reverting a terminal status
    if is_already_terminal and not is_new_status_terminal:
        logger.info(
            "Ignored stale callback '%s' for already terminal call %s",
            normalized_status,
            agent_call.id,
        )
        return {
            "status": "ignored",
            "call_id": agent_call.id,
            "call_status": agent_call.status,
            "detail": f"Stale callback '{normalized_status}' ignored for terminal call",
        }

    # If call is not yet terminal, update status and set ended_at when transitioning to terminal
    if not is_already_terminal:
        agent_call.status = normalized_status
        if is_new_status_terminal and not agent_call.ended_at:
            agent_call.ended_at = datetime.now(timezone.utc)

    # Set started_at only on the first answered / in-progress event
    if not agent_call.started_at and normalized_status == "in-progress":
        agent_call.started_at = datetime.now(timezone.utc)

    # Duration handling (valid for new or duplicate terminal callbacks)
    if is_new_status_terminal or is_already_terminal:
        if isinstance(call_duration, str) and call_duration.strip().isdigit():
            agent_call.duration = int(call_duration.strip())
        elif (
            agent_call.duration is None
            and agent_call.started_at
            and agent_call.ended_at
        ):
            started = (
                agent_call.started_at
                if agent_call.started_at.tzinfo
                else agent_call.started_at.replace(tzinfo=timezone.utc)
            )
            ended = (
                agent_call.ended_at
                if agent_call.ended_at.tzinfo
                else agent_call.ended_at.replace(tzinfo=timezone.utc)
            )
            agent_call.duration = max(
                0, int((ended - started).total_seconds())
            )

    # Store recording URL only when a valid HTTP/HTTPS URL with host is provided
    if isinstance(recording_url, str) and is_valid_recording_url(recording_url):
        agent_call.recording_url = recording_url.strip()

    # Atomically enqueue job in the same transaction if call is completed
    if normalized_status == "completed":
        try_enqueue_call_processing_job(db, agent_call)

    db.commit()
    db.refresh(agent_call)

    if normalized_status == "completed" and background_tasks is not None:
        background_tasks.add_task(
            run_worker_cycle,
            worker_id=f"voice-webhook-{agent_call.id}",
        )

    return {
        "status": "ok",
        "call_id": agent_call.id,
        "call_status": agent_call.status,
        "duration": agent_call.duration,
        "recording_url": agent_call.recording_url,
    }
