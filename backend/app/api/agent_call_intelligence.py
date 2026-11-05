from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from sqlalchemy.orm import Session

from backend.app.db.database import get_db

from backend.app.models.agent import Agent
from backend.app.models.lead import Lead
from backend.app.models.agent_call import AgentCall
from backend.app.models.user import User
from backend.app.utils.dependencies import get_current_user
from backend.app.utils.phone import normalize_phone

from backend.app.services.agent_call_analysis import (
    build_transcript_text,
)

from backend.app.services.agent_call_intelligence import (
    analyze_call_intelligence,
    create_agent_call_intelligence,
    get_agent_call_intelligence,
    update_agent_call_intelligence,
)

from backend.app.services.pipeline_automation import (
    automate_pipeline_stage,
)

from backend.app.schemas.agent_call_intelligence import (
    AgentCallIntelligenceCreate,
    AgentCallIntelligenceUpdate,
    AgentCallIntelligenceResponse,
)


router = APIRouter(
    prefix="/agents",
    tags=["Agent Call Intelligence"],
)


# ============================================================
# FIND MATCHING LEAD
# ============================================================

def find_matching_lead(
    db: Session,
    agent_call: AgentCall,
) -> Optional[Lead]:
    """
    Find matching lead in the same organization by normalized phone number.
    Uses indexed Lead.phone_normalized query rather than in-memory scanning.
    """
    caller_phone_norm = agent_call.caller_phone_normalized
    if not caller_phone_norm and agent_call.caller_phone:
        caller_phone_norm, _ = normalize_phone(agent_call.caller_phone)

    if not caller_phone_norm:
        return None

    candidates = [caller_phone_norm]
    if caller_phone_norm.startswith("+"):
        candidates.append(caller_phone_norm.lstrip("+"))
    else:
        candidates.append(f"+{caller_phone_norm}")

    return (
        db.query(Lead)
        .filter(
            Lead.organization_id == agent_call.organization_id,
            Lead.phone_normalized.in_(candidates),
        )
        .first()
    )


# ============================================================
# GET CALL INTELLIGENCE
# ============================================================

@router.get(
    "/{agent_id}/calls/{call_id}/intelligence",
    response_model=AgentCallIntelligenceResponse,
    status_code=status.HTTP_200_OK,
)
def get_call_intelligence_endpoint(
    agent_id: int,
    call_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # ========================================================
    # GET AND VALIDATE AGENT
    # ========================================================

    agent = (
        db.query(Agent)
        .filter(
            Agent.id == agent_id,
            Agent.organization_id == current_user.organization_id,
        )
        .first()
    )

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )

    # ========================================================
    # GET AND VALIDATE AGENT CALL
    # ========================================================

    agent_call = (
        db.query(AgentCall)
        .filter(
            AgentCall.id == call_id,
            AgentCall.agent_id == agent_id,
            AgentCall.organization_id == current_user.organization_id,
        )
        .first()
    )

    if not agent_call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent call not found",
        )

    # ========================================================
    # GET CALL INTELLIGENCE
    # ========================================================

    intelligence = get_agent_call_intelligence(
        db,
        call_id,
    )

    if not intelligence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Call intelligence not found",
        )

    return intelligence


# ============================================================
# ANALYZE CALL INTELLIGENCE
# ============================================================

@router.post(
    "/{agent_id}/calls/{call_id}/intelligence",
    response_model=AgentCallIntelligenceResponse,
    status_code=status.HTTP_200_OK,
)
def analyze_call_intelligence_endpoint(
    agent_id: int,
    call_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    # ========================================================
    # GET AGENT CALL
    # ========================================================

    agent_call = (
        db.query(AgentCall)
        .filter(
            AgentCall.id == call_id,
            AgentCall.agent_id == agent_id,
            AgentCall.organization_id
            == current_user.organization_id,
        )
        .first()
    )

    # ========================================================
    # VALIDATE AGENT CALL
    # ========================================================

    if not agent_call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent call not found",
        )

    # ========================================================
    # BUILD TRANSCRIPT
    # ========================================================

    transcript_text = build_transcript_text(
        db,
        call_id,
    )

    # ========================================================
    # CHECK TRANSCRIPT
    # ========================================================

    if not transcript_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No transcript available for this call",
        )

    # ========================================================
    # ANALYZE CALL WITH AI
    # ========================================================

    analysis = analyze_call_intelligence(
        transcript_text,
    )

    # ========================================================
    # FIND MATCHING LEAD
    # ========================================================

    lead = find_matching_lead(
        db,
        agent_call,
    )

    # ========================================================
    # AUTOMATIC PIPELINE UPDATE
    # ========================================================

    if lead:

        updated_lead = automate_pipeline_stage(
            db=db,
            lead=lead,
            lead_temperature=analysis.get(
                "lead_temperature"
            ),
            customer_intent=analysis.get(
                "customer_intent"
            ),
        )

    # ========================================================
    # CHECK EXISTING INTELLIGENCE
    # ========================================================

    existing_intelligence = (
        get_agent_call_intelligence(
            db,
            call_id,
        )
    )

    # ========================================================
    # UPDATE EXISTING INTELLIGENCE
    # ========================================================

    if existing_intelligence:

        intelligence_data = (
            AgentCallIntelligenceUpdate(
                sentiment=analysis.get(
                    "sentiment"
                ),

                lead_score=analysis.get(
                    "lead_score"
                ),

                lead_temperature=analysis.get(
                    "lead_temperature"
                ),

                customer_intent=analysis.get(
                    "customer_intent"
                ),

                objections=analysis.get(
                    "objections"
                ),

                buying_signals=analysis.get(
                    "buying_signals"
                ),

                recommended_action=analysis.get(
                    "recommended_action"
                ),
            )
        )

        updated_intelligence = (
            update_agent_call_intelligence(
                db,
                existing_intelligence,
                intelligence_data,
            )
        )

        return updated_intelligence

    # ========================================================
    # CREATE NEW INTELLIGENCE
    # ========================================================

    intelligence_data = (
        AgentCallIntelligenceCreate(
            sentiment=analysis.get(
                "sentiment"
            ),

            lead_score=analysis.get(
                "lead_score"
            ),

            lead_temperature=analysis.get(
                "lead_temperature"
            ),

            customer_intent=analysis.get(
                "customer_intent"
            ),

            objections=analysis.get(
                "objections"
            ),

            buying_signals=analysis.get(
                "buying_signals"
            ),

            recommended_action=analysis.get(
                "recommended_action"
            ),
        )
    )

    created_intelligence = (
        create_agent_call_intelligence(
            db,
            call_id,
            intelligence_data,
        )
    )

    return created_intelligence
