import os
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.app.models.agent import Agent
from backend.app.models.agent_call import AgentCall
from backend.app.services.voice_provider import VoiceProvider
from backend.app.services.twilio_voice_provider import TwilioVoiceProvider
from backend.app.services.mock_voice_provider import MockVoiceProvider


def get_voice_provider() -> VoiceProvider:
    provider_name = os.getenv("VOICE_PROVIDER", "").strip().lower()
    if provider_name == "mock":
        return MockVoiceProvider()
    return TwilioVoiceProvider()


def initiate_voice_call(
    db: Session,
    agent: Agent,
    agent_call: AgentCall,
    to_number: str,
    from_number: str,
):
    provider = get_voice_provider()

    try:
        result = provider.initiate_call(
            to_number=to_number,
            from_number=from_number,
            agent_id=agent.id,
            call_id=agent_call.id,
        )

        agent_call.provider_call_id = result["provider_call_id"]
        agent_call.status = result["status"]

        db.commit()
        db.refresh(agent_call)

        return agent_call

    except Exception:
        db.rollback()
        raise


def end_voice_call(
    db: Session,
    agent_call: AgentCall,
):
    if not agent_call.provider_call_id:
        raise ValueError(
            "Cannot end call: provider call ID is missing."
        )

    provider = get_voice_provider()

    try:
        result = provider.end_call(
            provider_call_id=agent_call.provider_call_id,
        )

        agent_call.status = result["status"]
        agent_call.ended_at = datetime.now(timezone.utc)

        if agent_call.started_at:
            started_at = agent_call.started_at

            # Handle a naive datetime if the database returns one.
            if started_at.tzinfo is None:
                started_at = started_at.replace(
                    tzinfo=timezone.utc
                )

            duration = (
                agent_call.ended_at - started_at
            )

            agent_call.duration = max(
                0,
                int(duration.total_seconds()),
            )

        db.commit()
        db.refresh(agent_call)

        return agent_call

    except Exception:
        db.rollback()
        raise
