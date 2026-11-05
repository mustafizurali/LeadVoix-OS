import logging
from typing import Optional
from sqlalchemy.orm import Session

from backend.app.db.database import SessionLocal
from backend.app.models.agent import Agent
from backend.app.models.agent_call import AgentCall
from backend.app.models.agent_call_intelligence import (
    AgentCallIntelligence,
)
from backend.app.models.agent_call_summary import AgentCallSummary
from backend.app.schemas.agent_call_intelligence import (
    AgentCallIntelligenceCreate,
    AgentCallIntelligenceUpdate,
)
from backend.app.services.agent_call_analysis import (
    build_transcript_text,
    analyze_call_transcript,
)

logger = logging.getLogger(__name__)


def create_agent_call_intelligence(
    db: Session,
    agent_call_id: int,
    intelligence_data: AgentCallIntelligenceCreate,
):
    intelligence = AgentCallIntelligence(
        agent_call_id=agent_call_id,
        **intelligence_data.model_dump(),
    )

    db.add(intelligence)
    db.commit()
    db.refresh(intelligence)

    return intelligence


def get_agent_call_intelligence(
    db: Session,
    agent_call_id: int,
):
    return (
        db.query(AgentCallIntelligence)
        .filter(
            AgentCallIntelligence.agent_call_id
            == agent_call_id
        )
        .first()
    )


def update_agent_call_intelligence(
    db: Session,
    intelligence: AgentCallIntelligence,
    intelligence_data: AgentCallIntelligenceUpdate,
):
    update_data = intelligence_data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(
            intelligence,
            field,
            value,
        )

    db.commit()
    db.refresh(intelligence)

    return intelligence


def analyze_call_intelligence(
    transcript_text: str,
):
    text = transcript_text.lower()

    sentiment = "neutral"
    lead_score = 50
    lead_temperature = "warm"
    customer_intent = "general_interest"
    objections = None
    buying_signals = None
    recommended_action = (
        "Send follow-up information"
    )

    # Positive buying signals
    positive_keywords = [
        "interested",
        "pricing",
        "price",
        "demo",
        "schedule",
        "buy",
        "purchase",
        "sign up",
        "get started",
    ]

    positive_matches = [
        keyword
        for keyword in positive_keywords
        if keyword in text
    ]

    if positive_matches:
        sentiment = "positive"
        lead_score += len(positive_matches) * 5

        buying_signals = (
            "Detected interest in: "
            + ", ".join(positive_matches)
        )

    # Strong buying intent
    strong_intent_keywords = [
        "schedule a demo",
        "book a demo",
        "get started",
        "ready to buy",
        "purchase",
    ]

    if any(
        keyword in text
        for keyword in strong_intent_keywords
    ):
        lead_score += 20
        lead_temperature = "hot"
        customer_intent = "high_purchase_intent"
        recommended_action = (
            "Contact the customer immediately "
            "and schedule a demo or sales call"
        )

    # Pricing interest
    elif (
        "pricing" in text
        or "price" in text
        or "cost" in text
    ):
        lead_score += 15
        lead_temperature = "hot"
        customer_intent = "pricing_interest"
        recommended_action = (
            "Send pricing details and schedule "
            "a follow-up call"
        )

    # Objections
    objection_keywords = [
        "too expensive",
        "expensive",
        "not interested",
        "think about it",
        "budget",
        "later",
        "not now",
    ]

    detected_objections = [
        keyword
        for keyword in objection_keywords
        if keyword in text
    ]

    if detected_objections:
        objections = (
            "Detected objections: "
            + ", ".join(detected_objections)
        )

        lead_score -= (
            len(detected_objections) * 10
        )

        if lead_score < 40:
            lead_temperature = "cold"

    # Negative sentiment
    negative_keywords = [
        "not interested",
        "stop calling",
        "no thanks",
        "don't call",
    ]

    if any(
        keyword in text
        for keyword in negative_keywords
    ):
        sentiment = "negative"
        lead_temperature = "cold"
        lead_score = min(lead_score, 20)
        customer_intent = "not_interested"
        recommended_action = (
            "Do not continue aggressive follow-up"
        )

    # Keep score between 0 and 100
    lead_score = max(
        0,
        min(lead_score, 100),
    )

    return {
        "sentiment": sentiment,
        "lead_score": lead_score,
        "lead_temperature": lead_temperature,
        "customer_intent": customer_intent,
        "objections": objections,
        "buying_signals": buying_signals,
        "recommended_action": recommended_action,
    }


def process_call_intelligence_worker(
    agent_id: int,
    call_id: int,
) -> Optional[AgentCallIntelligence]:
    """
    Safely executes post-call intelligence analysis in a separate worker session.
    Enforces row-level serialization via with_for_update(), tenant isolation,
    atomic intelligence & summary persistence, and failure handling.
    """
    worker_db = SessionLocal()
    try:
        # 1. Acquire exclusive row lock on the exact AgentCall row
        try:
            locked_agent_call = (
                worker_db.query(AgentCall)
                .filter(AgentCall.id == call_id)
                .with_for_update()
                .first()
            )
        except Exception as lock_exc:
            worker_db.rollback()
            logger.error(
                "Post-call intelligence: Lock acquisition failed for call_id=%s: %s",
                call_id,
                type(lock_exc).__name__,
            )
            return None

        if not locked_agent_call:
            worker_db.rollback()
            logger.warning(
                "Post-call intelligence: AgentCall %s not found under lock",
                call_id,
            )
            return None

        agent_call = locked_agent_call

        # 2. Verify Agent and organization ownership after acquiring the lock
        agent = worker_db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            worker_db.rollback()
            logger.warning("Post-call intelligence: Agent %s not found", agent_id)
            return None

        if agent_call.agent_id != agent.id:
            worker_db.rollback()
            logger.warning(
                "Post-call intelligence: AgentCall %s does not belong to Agent %s",
                call_id,
                agent_id,
            )
            return None

        if agent_call.organization_id != agent.organization_id:
            worker_db.rollback()
            logger.warning(
                "Post-call intelligence: Organization mismatch for call %s and agent %s",
                call_id,
                agent_id,
            )
            return None

        # 3. Verify that call status is exactly completed
        if agent_call.status != "completed":
            worker_db.rollback()
            logger.info(
                "Post-call intelligence: Call %s has non-completed status '%s', skipping analysis.",
                call_id,
                agent_call.status,
            )
            return None

        # 4. Re-check existing AgentCallIntelligence under the lock
        existing_intelligence = (
            worker_db.query(AgentCallIntelligence)
            .filter(AgentCallIntelligence.agent_call_id == call_id)
            .first()
        )
        if existing_intelligence:
            worker_db.rollback()
            logger.info(
                "Post-call intelligence: Call %s already analyzed, skipping.",
                call_id,
            )
            return existing_intelligence

        # 4. Retrieve and validate transcript strictly scoped to this call
        transcript_text = build_transcript_text(worker_db, call_id)
        if not transcript_text and agent_call.transcript:
            transcript_text = agent_call.transcript.strip()

        if not transcript_text:
            worker_db.rollback()
            logger.info(
                "Post-call intelligence: Call %s has empty transcript, skipping analysis.",
                call_id,
            )
            return None

        # 5. Perform analysis using existing services (no CRM lead mutation)
        analysis = analyze_call_intelligence(transcript_text)
        summary_data = analyze_call_transcript(transcript_text)

        # 6. Atomic Intelligence and Summary Persistence:
        # Both must succeed together; failure of either rolls back both.
        created_intelligence = AgentCallIntelligence(
            agent_call_id=call_id,
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
            .filter(AgentCallSummary.agent_call_id == call_id)
            .first()
        )
        if not existing_summary:
            created_summary = AgentCallSummary(
                agent_call_id=call_id,
                summary=summary_data.get("summary"),
                key_points=summary_data.get("key_points"),
                outcome=summary_data.get("outcome"),
                next_action=summary_data.get("next_action"),
            )
            worker_db.add(created_summary)

        worker_db.commit()
        worker_db.refresh(created_intelligence)

        logger.info(
            "Post-call intelligence and summary atomically committed for call %s",
            call_id,
        )
        return created_intelligence

    except Exception as exc:
        worker_db.rollback()
        # Handle concurrency race where a competing worker committed first
        if "unique" in str(exc).lower() or "integrity" in type(exc).__name__.lower():
            logger.info(
                "Post-call intelligence: Concurrent insert race resolved via unique constraint for call %s",
                call_id,
            )
            existing = (
                worker_db.query(AgentCallIntelligence)
                .filter(AgentCallIntelligence.agent_call_id == call_id)
                .first()
            )
            if existing:
                return existing

        logger.error(
            "Post-call intelligence failed for call_id=%s, agent_id=%s: %s",
            call_id,
            agent_id,
            type(exc).__name__,
        )
        return None
    finally:
        worker_db.close()
