
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.db.database import get_db
from backend.app.models.agent import Agent
from backend.app.models.user import User
from backend.app.schemas.agent_call import (
    AgentCallCreate,
    AgentCallResponse,
    AgentCallUpdate,
)
from backend.app.services.agent_call import (
    create_agent_call,
    get_agent_calls,
    get_agent_call,
    update_agent_call,
    delete_agent_call,
)
from backend.app.services.voice_call import (
    initiate_voice_call,
    end_voice_call,
)
from backend.app.utils.dependencies import get_current_user


router = APIRouter(
    prefix="/agents",
    tags=["Agent Calls"],
)


def get_authorized_agent(
    db: Session,
    agent_id: int,
    organization_id: int,
) -> Agent:
    agent = (
        db.query(Agent)
        .filter(
            Agent.id == agent_id,
            Agent.organization_id == organization_id,
        )
        .first()
    )

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )

    return agent


def get_authorized_call(
    db: Session,
    agent_id: int,
    call_id: int,
    organization_id: int,
):
    agent_call = get_agent_call(db, call_id)

    if (
        not agent_call
        or agent_call.agent_id != agent_id
        or agent_call.organization_id != organization_id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent call not found",
        )

    return agent_call


@router.post(
    "/{agent_id}/calls",
    response_model=AgentCallResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_call(
    agent_id: int,
    call_data: AgentCallCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    agent = get_authorized_agent(
        db, agent_id, current_user.organization_id
    )

    return create_agent_call(
        db,
        agent_id,
        agent.organization_id,
        call_data,
    )


@router.post(
    "/{agent_id}/calls/{call_id}/initiate",
    response_model=AgentCallResponse,
)
def initiate_call(
    agent_id: int,
    call_id: int,
    to_number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    agent = get_authorized_agent(
        db, agent_id, current_user.organization_id
    )

    agent_call = get_authorized_call(
        db,
        agent_id,
        call_id,
        current_user.organization_id,
    )

    if agent_call.provider_call_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This call has already been initiated",
        )

    try:
        return initiate_voice_call(
            db=db,
            agent=agent,
            agent_call=agent_call,
            to_number=to_number,
            from_number=settings.TWILIO_PHONE_NUMBER,
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The voice provider could not initiate the call",
        ) from exc
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save the call status",
        ) from exc


@router.post(
    "/{agent_id}/calls/{call_id}/end",
    response_model=AgentCallResponse,
)
def end_call(
    agent_id: int,
    call_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_authorized_agent(
        db, agent_id, current_user.organization_id
    )

    agent_call = get_authorized_call(
        db,
        agent_id,
        call_id,
        current_user.organization_id,
    )

    if not agent_call.provider_call_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Call has not been initiated",
        )

    try:
        return end_voice_call(
            db=db,
            agent_call=agent_call,
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The voice provider could not end the call",
        ) from exc
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save the call status",
        ) from exc


@router.get(
    "/{agent_id}/calls",
    response_model=List[AgentCallResponse],
)
def get_calls(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_authorized_agent(
        db, agent_id, current_user.organization_id
    )

    return get_agent_calls(db, agent_id)


@router.get(
    "/{agent_id}/calls/{call_id}",
    response_model=AgentCallResponse,
)
def get_call(
    agent_id: int,
    call_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_authorized_call(
        db,
        agent_id,
        call_id,
        current_user.organization_id,
    )


@router.put(
    "/{agent_id}/calls/{call_id}",
    response_model=AgentCallResponse,
)
def update_call(
    agent_id: int,
    call_id: int,
    call_data: AgentCallUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    agent_call = get_authorized_call(
        db,
        agent_id,
        call_id,
        current_user.organization_id,
    )

    return update_agent_call(
        db,
        agent_call,
        call_data,
    )


@router.delete(
    "/{agent_id}/calls/{call_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_call(
    agent_id: int,
    call_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    agent_call = get_authorized_call(
        db,
        agent_id,
        call_id,
        current_user.organization_id,
    )

    delete_agent_call(db, agent_call)