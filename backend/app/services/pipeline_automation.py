from datetime import datetime, timezone
from decimal import Decimal
import logging
from typing import Optional

from sqlalchemy.orm import Session

from backend.app.models.agent_call import AgentCall
from backend.app.models.contact import Contact
from backend.app.models.deal import Deal
from backend.app.models.deal_stage_history import DealStageHistory
from backend.app.models.lead import Lead
from backend.app.models.pipeline import Pipeline
from backend.app.models.pipeline_stage import PipelineStage
from backend.app.models.user import User

logger = logging.getLogger(__name__)


def get_organization_pipeline(
    db: Session,
    organization_id: int,
    pipeline_id: Optional[int] = None,
) -> Optional[Pipeline]:
    """
    Finds the active pipeline for the organization.
    Prioritizes explicit pipeline_id, then is_default == True, then first active pipeline.
    """
    if pipeline_id:
        p = (
            db.query(Pipeline)
            .filter(
                Pipeline.id == pipeline_id,
                Pipeline.organization_id == organization_id,
                Pipeline.is_active == True,
            )
            .first()
        )
        if p:
            return p

    # Find default active pipeline
    default_p = (
        db.query(Pipeline)
        .filter(
            Pipeline.organization_id == organization_id,
            Pipeline.is_default == True,
            Pipeline.is_active == True,
        )
        .first()
    )
    if default_p:
        return default_p

    # Fallback to first active pipeline
    return (
        db.query(Pipeline)
        .filter(
            Pipeline.organization_id == organization_id,
            Pipeline.is_active == True,
        )
        .order_by(Pipeline.id.asc())
        .first()
    )


def find_pipeline_stage_for_signal(
    db: Session,
    pipeline: Pipeline,
    signal_name: Optional[str],
) -> Optional[PipelineStage]:
    """
    Discovers the matching stage in the organization's pipeline for a given signal:
    'qualified', 'interested', 'follow_up', or 'lost'.
    Does NOT invent stages; returns None if no matching stage is configured.
    """
    if not pipeline or not signal_name:
        return None

    stages = (
        db.query(PipelineStage)
        .filter(
            PipelineStage.pipeline_id == pipeline.id,
            PipelineStage.is_active == True,
        )
        .order_by(PipelineStage.position.asc())
        .all()
    )

    if not stages:
        return None

    sig = signal_name.lower().strip()

    # 1. Lost stage matching
    if sig in ("lost", "not_interested"):
        for stage in stages:
            if stage.stage_type == "LOST":
                return stage
        for stage in stages:
            name_lower = stage.name.lower()
            if "lost" in name_lower or "closed lost" in name_lower:
                return stage
        return None

    # 2. Qualified stage matching
    if sig in ("qualified", "high_purchase_intent", "demo"):
        for stage in stages:
            name_lower = stage.name.lower()
            if any(k in name_lower for k in ["qualif", "demo", "opportunity"]):
                return stage
        for stage in stages:
            if stage.stage_type == "NORMAL" and stage.position > 0 and stage.probability >= 40:
                return stage
        normal_stages = [s for s in stages if s.stage_type == "NORMAL"]
        if len(normal_stages) > 1:
            return normal_stages[1]
        return normal_stages[0] if normal_stages else None

    # 3. Interested stage matching
    if sig in ("interested", "pricing_interest"):
        for stage in stages:
            name_lower = stage.name.lower()
            if any(k in name_lower for k in ["interest", "pricing", "evaluat"]):
                return stage
        for stage in stages:
            name_lower = stage.name.lower()
            if any(k in name_lower for k in ["contact", "discovery"]):
                return stage
        normal_stages = [s for s in stages if s.stage_type == "NORMAL"]
        return normal_stages[0] if normal_stages else None

    # 4. Follow-up stage matching
    if sig in ("follow_up", "warm"):
        for stage in stages:
            name_lower = stage.name.lower()
            if any(k in name_lower for k in ["follow", "meeting", "contact", "call"]):
                return stage
        for stage in stages:
            name_lower = stage.name.lower()
            if "interest" in name_lower:
                return stage
        normal_stages = [s for s in stages if s.stage_type == "NORMAL"]
        if len(normal_stages) > 1:
            return normal_stages[1]
        return normal_stages[0] if normal_stages else None

    return None


def record_deal_stage_transition(
    db: Session,
    deal: Deal,
    from_stage_id: Optional[int],
    to_stage_id: int,
    user_id: Optional[int] = None,
    entry_type: str = "transition",
) -> Optional[DealStageHistory]:
    """
    Safely records a deal stage history transition and closes previous active history record.
    Prevents duplicate transitions for the same stage.
    """
    if from_stage_id == to_stage_id and entry_type != "initial":
        return None

    now = datetime.now(timezone.utc)

    # Close previous active history entry
    prev_entry = (
        db.query(DealStageHistory)
        .filter(
            DealStageHistory.organization_id == deal.organization_id,
            DealStageHistory.deal_id == deal.id,
            DealStageHistory.exited_at.is_(None),
        )
        .first()
    )
    if prev_entry:
        if prev_entry.to_stage_id == to_stage_id:
            # Already in this stage actively, do not create duplicate
            return prev_entry
        prev_entry.exited_at = now
        if prev_entry.entered_at:
            duration = int((now - prev_entry.entered_at).total_seconds())
            prev_entry.duration_seconds = max(0, duration)

    history = DealStageHistory(
        organization_id=deal.organization_id,
        deal_id=deal.id,
        from_stage_id=from_stage_id,
        to_stage_id=to_stage_id,
        entered_at=now,
        exited_at=None,
        duration_seconds=None,
        changed_by_user_id=user_id or deal.owner_id,
        entry_type=entry_type,
        is_verified_transition=True,
    )
    db.add(history)
    return history


def has_strong_purchase_or_qualification_signal(
    analysis: Optional[dict] = None,
    summary_data: Optional[dict] = None,
    lead: Optional[Lead] = None,
) -> bool:
    """
    Evaluates whether a call contains strong purchase intent or sales qualification signal.
    """
    analysis = analysis or {}
    summary_data = summary_data or {}
    intent = (analysis.get("customer_intent") or "").lower().strip()
    temp = (analysis.get("lead_temperature") or "").lower().strip()
    outcome = (summary_data.get("outcome") or "").lower().strip()
    lead_status = (lead.status or "").lower().strip() if lead else ""

    if intent in ("not_interested", "lost") or outcome in ("not interested", "not_interested"):
        return False

    if intent in ("high_purchase_intent", "demo"):
        return True
    if temp == "hot" and intent != "pricing_interest":
        return True
    if outcome in ("demo scheduled", "demo_scheduled"):
        return True
    if lead_status == "qualified":
        return True

    return False


def build_deal_description(
    analysis: Optional[dict] = None,
    summary_data: Optional[dict] = None,
    agent_call: Optional[AgentCall] = None,
) -> str:
    """
    Constructs an informative deal description from call intelligence without inventing commitments.
    """
    analysis = analysis or {}
    summary_data = summary_data or {}
    parts = []
    summary_text = summary_data.get("summary")
    if summary_text and summary_text.strip():
        parts.append(f"Call Summary: {summary_text.strip()}")

    intent = analysis.get("customer_intent")
    score = analysis.get("lead_score")
    temp = analysis.get("lead_temperature")
    metrics = []
    if score is not None:
        metrics.append(f"Score: {score}")
    if temp:
        metrics.append(f"Temp: {temp}")
    if intent:
        metrics.append(f"Intent: {intent}")
    if metrics:
        parts.append("Qualification Metrics: " + " | ".join(metrics))

    rec_action = analysis.get("recommended_action") or summary_data.get("next_action")
    if rec_action and rec_action.strip():
        parts.append(f"Recommended Next Step: {rec_action.strip()}")

    if agent_call and agent_call.id:
        parts.append(f"Source Call: Agent Call #{agent_call.id}")

    return "\n\n".join(parts)


def automate_pipeline_and_deal(
    db: Session,
    organization_id: int,
    agent_call: Optional[AgentCall] = None,
    analysis: Optional[dict] = None,
    summary_data: Optional[dict] = None,
    matched_lead: Optional[Lead] = None,
    matched_contact: Optional[Contact] = None,
    caller_display_name: str = "Customer",
    auto_commit: bool = False,
) -> Optional[Deal]:
    """
    Discovers the organization's pipeline and stages, maps call intelligence to
    the appropriate stage, and safely creates or updates Deals.
    """
    analysis = analysis or {}
    summary_data = summary_data or {}

    pipeline = get_organization_pipeline(db, organization_id)
    if not pipeline:
        logger.info("No active pipeline found for organization %s; skipping deal automation.", organization_id)
        return None

    # Determine target stage signal
    intent = (analysis.get("customer_intent") or "").lower().strip()
    outcome = (summary_data.get("outcome") or "").lower().strip()
    lead_temp = (analysis.get("lead_temperature") or "").lower().strip()
    lead_status = (matched_lead.status or "").lower().strip() if matched_lead else ""

    if intent in ("not_interested", "lost") or outcome in ("not interested", "not_interested") or lead_status == "lost":
        target_signal = "lost"
    elif intent in ("high_purchase_intent", "demo") or (lead_temp == "hot" and intent != "pricing_interest" and lead_status != "interested") or lead_status == "qualified":
        target_signal = "qualified"
    elif intent == "pricing_interest" or outcome in ("interested", "pricing") or lead_status == "interested":
        target_signal = "interested"
    elif outcome in ("follow-up required", "follow_up_required", "follow_up", "follow up") or lead_temp == "warm" or lead_status == "follow_up":
        target_signal = "follow_up"
    else:
        target_signal = None

    target_stage = find_pipeline_stage_for_signal(db, pipeline, target_signal) if target_signal else None

    # Check for existing open Deal
    existing_deal = None
    if matched_lead and matched_lead.id:
        existing_deal = (
            db.query(Deal)
            .filter(
                Deal.organization_id == organization_id,
                Deal.lead_id == matched_lead.id,
                Deal.status == "OPEN",
            )
            .order_by(Deal.id.desc())
            .first()
        )
    if not existing_deal and matched_contact and matched_contact.id:
        existing_deal = (
            db.query(Deal)
            .filter(
                Deal.organization_id == organization_id,
                Deal.contact_id == matched_contact.id,
                Deal.status == "OPEN",
            )
            .order_by(Deal.id.desc())
            .first()
        )

    # 1. Existing Deal Reuse and Safe Stage Transition
    if existing_deal:
        if target_signal == "lost" and target_stage:
            if existing_deal.stage_id != target_stage.id:
                prev_stage_id = existing_deal.stage_id
                existing_deal.stage_id = target_stage.id
                existing_deal.status = "LOST"
                record_deal_stage_transition(db, existing_deal, prev_stage_id, target_stage.id)
        elif target_stage and target_stage.id != existing_deal.stage_id:
            current_stage = (
                db.query(PipelineStage).filter(PipelineStage.id == existing_deal.stage_id).first()
                if existing_deal.stage_id
                else None
            )
            should_advance = False
            if not current_stage:
                should_advance = True
            elif target_signal == "qualified" and target_stage.position >= current_stage.position:
                should_advance = True
            elif target_signal in ("interested", "follow_up") and current_stage.position <= target_stage.position:
                should_advance = True

            if should_advance:
                prev_stage_id = existing_deal.stage_id
                existing_deal.stage_id = target_stage.id
                if target_stage.stage_type == "WON":
                    existing_deal.status = "WON"
                elif target_stage.stage_type == "LOST":
                    existing_deal.status = "LOST"
                else:
                    existing_deal.status = "OPEN"
                record_deal_stage_transition(db, existing_deal, prev_stage_id, target_stage.id)

        # Backfill linked lead / contact if missing
        if matched_lead and not existing_deal.lead_id:
            existing_deal.lead_id = matched_lead.id
        if matched_contact and not existing_deal.contact_id:
            existing_deal.contact_id = matched_contact.id

        if auto_commit:
            db.commit()
            db.refresh(existing_deal)
        return existing_deal

    # 2. New Deal Creation (ONLY if strong purchase intent or qualification exists and not lost)
    is_qualified = has_strong_purchase_or_qualification_signal(analysis, summary_data, matched_lead)
    if is_qualified and target_signal != "lost":
        stage_to_assign = target_stage
        if not stage_to_assign:
            normal_stages = (
                db.query(PipelineStage)
                .filter(PipelineStage.pipeline_id == pipeline.id, PipelineStage.is_active == True)
                .order_by(PipelineStage.position.asc())
                .all()
            )
            stage_to_assign = normal_stages[0] if normal_stages else None

        owner_id = (
            (matched_lead.owner_id if matched_lead else None)
            or (matched_contact.owner_id if matched_contact else None)
        )
        if not owner_id:
            org_user = (
                db.query(User.id)
                .filter(User.organization_id == organization_id)
                .order_by(User.id.asc())
                .first()
            )
            if org_user:
                owner_id = org_user[0]

        company_id_val = None
        if matched_lead and matched_lead.company_id:
            company_id_val = matched_lead.company_id
        elif matched_contact and matched_contact.company_id:
            company_id_val = matched_contact.company_id

        new_deal = Deal(
            title=f"Deal: {caller_display_name}",
            amount=Decimal("0.00"),
            currency="USD",
            status="OPEN",
            expected_close_date=None,
            description=build_deal_description(analysis, summary_data, agent_call),
            organization_id=organization_id,
            pipeline_id=pipeline.id,
            stage_id=stage_to_assign.id if stage_to_assign else None,
            lead_id=matched_lead.id if matched_lead else None,
            contact_id=matched_contact.id if matched_contact else None,
            company_id=company_id_val,
            owner_id=owner_id,
        )
        db.add(new_deal)
        db.flush()

        if stage_to_assign:
            record_deal_stage_transition(
                db,
                new_deal,
                from_stage_id=None,
                to_stage_id=stage_to_assign.id,
                user_id=owner_id,
                entry_type="initial",
            )

        if auto_commit:
            db.commit()
            db.refresh(new_deal)
        return new_deal

    return None


def automate_pipeline_stage(
    db: Session,
    lead: Lead,
    lead_temperature: str,
    customer_intent: str,
    auto_commit: bool = True,
):
    # Normalize AI values
    lead_temperature = (
        lead_temperature.lower().strip()
        if lead_temperature
        else ""
    )

    customer_intent = (
        customer_intent.lower().strip()
        if customer_intent
        else ""
    )

    # Intent has higher priority
    if customer_intent == "not_interested":
        lead.status = "lost"
    elif customer_intent == "high_purchase_intent":
        lead.status = "qualified"
    elif customer_intent == "pricing_interest":
        lead.status = "interested"
    elif lead_temperature == "hot":
        lead.status = "qualified"
    elif lead_temperature == "warm":
        lead.status = "follow_up"
    elif lead_temperature == "cold":
        lead.status = "cold"

    # Also synchronize pipeline deal if configured
    automate_pipeline_and_deal(
        db=db,
        organization_id=lead.organization_id,
        agent_call=None,
        analysis={
            "customer_intent": customer_intent,
            "lead_temperature": lead_temperature,
        },
        matched_lead=lead,
        caller_display_name=f"{lead.first_name} {lead.last_name or ''}".strip(),
        auto_commit=False,
    )

    if auto_commit:
        db.commit()
        db.refresh(lead)

    return lead
