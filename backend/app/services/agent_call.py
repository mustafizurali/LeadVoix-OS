
from typing import List, Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.app.models.agent_call import AgentCall
from backend.app.schemas.agent_call import (
    AgentCallCreate,
    AgentCallUpdate,
)


def create_agent_call(
    db: Session,
    agent_id: int,
    organization_id: int,
    call_data: AgentCallCreate,
) -> AgentCall:
    agent_call = AgentCall(
        agent_id=agent_id,
        organization_id=organization_id,
        caller_name=call_data.caller_name,
        caller_phone=call_data.caller_phone,
        direction=call_data.direction or "inbound",
        status="queued",
    )

    try:
        db.add(agent_call)
        db.commit()
        db.refresh(agent_call)
        return agent_call
    except SQLAlchemyError:
        db.rollback()
        raise


def get_agent_calls(
    db: Session,
    agent_id: int,
) -> List[AgentCall]:
    return (
        db.query(AgentCall)
        .filter(AgentCall.agent_id == agent_id)
        .order_by(AgentCall.created_at.desc())
        .all()
    )


def get_agent_call(
    db: Session,
    call_id: int,
) -> Optional[AgentCall]:
    return (
        db.query(AgentCall)
        .filter(AgentCall.id == call_id)
        .first()
    )


def update_agent_call(
    db: Session,
    agent_call: AgentCall,
    call_data: AgentCallUpdate,
) -> AgentCall:
    update_data = call_data.model_dump(
        exclude_unset=True,
        exclude={
            "provider_call_id",
            "status",
            "started_at",
            "ended_at",
            "duration",
        },
    )

    for field, value in update_data.items():
        setattr(agent_call, field, value)

    try:
        db.commit()
        db.refresh(agent_call)
        return agent_call
    except SQLAlchemyError:
        db.rollback()
        raise


def delete_agent_call(
    db: Session,
    agent_call: AgentCall,
) -> None:
    try:
        db.delete(agent_call)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise