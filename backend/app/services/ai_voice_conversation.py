import logging
import os
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

try:
    from openai import OpenAI, OpenAIError, APITimeoutError
    _OPENAI_AVAILABLE = True
except ImportError:
    OpenAI = None  # type: ignore[assignment]
    OpenAIError = Exception  # type: ignore[assignment, misc]
    APITimeoutError = Exception  # type: ignore[assignment, misc]
    _OPENAI_AVAILABLE = False

from backend.app.core.config import settings
from backend.app.models.agent import Agent
from backend.app.models.agent_call import AgentCall
from backend.app.models.agent_knowledge import AgentKnowledge
from backend.app.models.agent_call_transcript import AgentCallTranscript
from backend.app.services.agent_call_transcript import get_agent_call_transcripts


logger = logging.getLogger(__name__)


def is_openai_available() -> bool:
    """Returns True if the OpenAI SDK is installed and available in the environment."""
    return _OPENAI_AVAILABLE


def get_openai_client(
    api_key: Optional[str] = None,
    timeout: Optional[float] = None,
) -> Any:
    """
    Initializes and returns an OpenAI client instance.
    Validates that the OpenAI SDK is installed and that a non-empty API key is present.
    Raises RuntimeError if the package is missing, or ValueError if the API key is missing.
    """
    if not _OPENAI_AVAILABLE or OpenAI is None:
        raise RuntimeError(
            "The 'openai' package is not installed. Please install it using 'pip install -r backend/requirements.txt'."
        )

    if api_key is not None:
        resolved_key = api_key.strip()
    else:
        resolved_key = (getattr(settings, "OPENAI_API_KEY", "") or "").strip()

    if not resolved_key:
        raise ValueError("OpenAI API key is missing or unconfigured.")

    client_timeout = timeout if timeout is not None else get_openai_timeout()
    return OpenAI(api_key=resolved_key, timeout=client_timeout)


# Configurable timeout strictly bounded between 6.0 and 8.0 seconds for telephony safety
def get_openai_timeout() -> float:
    raw = os.getenv("OPENAI_TIMEOUT_SECONDS", "7.0")
    try:
        val = float(raw)
        return max(6.0, min(8.0, val))
    except (ValueError, TypeError):
        return 7.0


OPENAI_MODEL = os.getenv("OPENAI_VOICE_MODEL", "gpt-4o-mini")

FALLBACK_RESPONSE = (
    "I apologize, but I am having trouble processing your request right now. "
    "Please let me know how else I can assist you."
)

TIMEOUT_RESPONSE = (
    "I apologize, that took a moment too long to process. "
    "Could you please repeat what you said?"
)

EMPTY_INPUT_RESPONSE = (
    "I did not hear anything. Could you please repeat that?"
)


# Safe maximum knowledge context size to prevent oversized prompts
MAX_KNOWLEDGE_CHARS = int(os.getenv("MAX_KNOWLEDGE_CHARS", "3000"))


def get_default_system_prompt(agent: Optional[Agent] = None) -> str:
    agent_name = (agent.name.strip() if agent and agent.name else "LeadVoix Voice Assistant")
    return (
        f"You are {agent_name}, an artificial intelligence voice assistant for LeadVoix. "
        "You are speaking with a customer on a telephone call. "
        "Keep all responses conversational, natural, and concise (typically 1 to 3 short sentences). "
        "Do not use markdown, emojis, bullet points, or special formatting that cannot be spoken aloud."
    )


def build_system_prompt(
    db: Session,
    agent: Agent,
    max_knowledge_chars: int = MAX_KNOWLEDGE_CHARS,
) -> str:
    if not agent:
        return get_default_system_prompt()

    if agent.system_prompt and agent.system_prompt.strip():
        base_prompt = agent.system_prompt.strip()
    else:
        base_prompt = get_default_system_prompt(agent)

    # Validate agent has valid identifiers
    if getattr(agent, "id", None) is None or getattr(agent, "organization_id", None) is None:
        return base_prompt

    # Retrieve only active knowledge items belonging to the exact agent and organization
    knowledge_items = (
        db.query(AgentKnowledge)
        .join(Agent, AgentKnowledge.agent_id == Agent.id)
        .filter(
            AgentKnowledge.agent_id == agent.id,
            Agent.id == agent.id,
            Agent.organization_id == agent.organization_id,
            AgentKnowledge.is_active == True,
        )
        .order_by(AgentKnowledge.id.asc())
        .all()
    )

    if knowledge_items:
        knowledge_sections = []
        current_chars = 0
        for item in knowledge_items:
            content = (item.content or "").strip()
            if not content:
                continue
            title = (item.title or "Knowledge").strip()
            section = f"[{title}]: {content}"

            # Truncate at item boundary if adding the whole section exceeds limit
            section_len = len(section) + 2
            if current_chars + section_len > max_knowledge_chars:
                if not knowledge_sections:
                    prefix = f"[{title}]: "
                    avail = max_knowledge_chars - len(prefix)
                    if avail > 20:
                        knowledge_sections.append(f"{prefix}{content[:avail].rstrip()}...")
                break

            knowledge_sections.append(section)
            current_chars += section_len

        if knowledge_sections:
            base_prompt += (
                "\n\nReference Knowledge:\n"
                + "\n\n".join(knowledge_sections)
            )

    return base_prompt


def build_conversation_messages(
    db: Session,
    agent: Agent,
    agent_call: AgentCall,
    user_speech: str,
    max_history_turns: int = 10,
    max_knowledge_chars: int = MAX_KNOWLEDGE_CHARS,
) -> List[Dict[str, str]]:
    messages: List[Dict[str, str]] = []

    # 1. System prompt with scoped knowledge
    system_content = build_system_prompt(db, agent, max_knowledge_chars=max_knowledge_chars)
    messages.append({"role": "system", "content": system_content})

    # 2. Conversation history strictly scoped to the exact call, agent, and organization
    if (
        agent_call
        and agent
        and getattr(agent_call, "id", None) is not None
        and getattr(agent, "id", None) is not None
        and getattr(agent_call, "agent_id", None) == agent.id
        and getattr(agent_call, "organization_id", None) == agent.organization_id
    ):
        # Transcripts verified via database join ensuring exact agent and organization ownership
        transcripts = (
            db.query(AgentCallTranscript)
            .join(AgentCall, AgentCallTranscript.agent_call_id == AgentCall.id)
            .filter(
                AgentCallTranscript.agent_call_id == agent_call.id,
                AgentCall.id == agent_call.id,
                AgentCall.agent_id == agent.id,
                AgentCall.organization_id == agent.organization_id,
            )
            .order_by(AgentCallTranscript.id.asc())
            .all()
        )

        if transcripts:
            recent_transcripts = (
                transcripts[-max_history_turns:]
                if len(transcripts) > max_history_turns
                else transcripts
            )
            for t in recent_transcripts:
                speaker = (t.speaker or "").strip().lower()
                msg = (t.message or "").strip()
                if not msg:
                    continue

                if speaker in ("agent", "assistant"):
                    messages.append({"role": "assistant", "content": msg})
                elif speaker in ("user", "caller", "customer", "lead"):
                    messages.append({"role": "user", "content": msg})
    else:
        logger.warning(
            "AgentCall %s does not match agent %s context; omitting history.",
            getattr(agent_call, "id", None),
            getattr(agent, "id", None),
        )

    # 3. Customer speech as untrusted user role message (never interpolated into system prompt)
    clean_speech = (user_speech or "").strip()[:1000]
    messages.append({"role": "user", "content": clean_speech})

    return messages


def generate_ai_voice_response(
    db: Session,
    agent: Agent,
    agent_call: AgentCall,
    user_speech: str,
    openai_client: Optional[Any] = None,
) -> str:
    clean_speech = (user_speech or "").strip()[:1000]
    if not clean_speech:
        return EMPTY_INPUT_RESPONSE

    # Deterministic mock response for offline testing or mock provider
    is_mock_mode = (
        os.getenv("VOICE_PROVIDER", "").strip().lower() == "mock"
        or os.getenv("OPENAI_MOCK", "").strip().lower() in ("true", "1")
    )
    if is_mock_mode:
        agent_name = agent.name if agent and agent.name else "LeadVoix AI"
        return f"Mock response from {agent_name}: I understood '{clean_speech}'."

    # Check OpenAI SDK availability when no custom client is provided
    if not _OPENAI_AVAILABLE and openai_client is None:
        logger.error(
            "OpenAI SDK is not available in environment for call_id=%s; returning fallback response.",
            getattr(agent_call, "id", None),
        )
        return FALLBACK_RESPONSE

    # Validate API key
    api_key = getattr(settings, "OPENAI_API_KEY", None)
    if (not api_key or not str(api_key).strip()) and openai_client is None:
        logger.warning(
            "OpenAI API key missing or unconfigured for call_id=%s",
            getattr(agent_call, "id", None),
        )
        return FALLBACK_RESPONSE

    timeout = get_openai_timeout()
    messages = build_conversation_messages(db, agent, agent_call, clean_speech)

    try:
        client = openai_client or get_openai_client(
            api_key=str(api_key).strip() if api_key else None,
            timeout=timeout,
        )

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            max_tokens=150,
            temperature=0.7,
            timeout=timeout,
        )

        if not response.choices:
            logger.warning(
                "OpenAI returned empty choices for call_id=%s",
                getattr(agent_call, "id", None),
            )
            return FALLBACK_RESPONSE

        reply = response.choices[0].message.content
        if not reply or not reply.strip():
            logger.warning(
                "OpenAI response content empty for call_id=%s",
                getattr(agent_call, "id", None),
            )
            return FALLBACK_RESPONSE

        return reply.strip()

    except APITimeoutError:
        logger.warning(
            "OpenAI API call timed out after %ss for call_id=%s",
            timeout,
            getattr(agent_call, "id", None),
        )
        return TIMEOUT_RESPONSE

    except OpenAIError as exc:
        logger.error(
            "OpenAI error for call_id=%s: %s",
            getattr(agent_call, "id", None),
            exc.__class__.__name__,
        )
        return FALLBACK_RESPONSE

    except Exception as exc:
        logger.error(
            "Unexpected error generating AI response for call_id=%s: %s",
            getattr(agent_call, "id", None),
            exc.__class__.__name__,
        )
        return FALLBACK_RESPONSE
