from typing import List

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from sqlalchemy.orm import Session

from backend.app.db.database import get_db
from backend.app.models.agent_call import AgentCall
from backend.app.models.user import User
from backend.app.utils.dependencies import get_current_user

from backend.app.services.follow_up_task import (
    create_follow_up_task,
    get_follow_up_task,
    get_follow_up_tasks_by_call,
    update_follow_up_task,
)

from backend.app.schemas.follow_up_task import (
    FollowUpTaskCreate,
    FollowUpTaskUpdate,
    FollowUpTaskResponse,
)


router = APIRouter(
    prefix="/agents",
    tags=["Follow-up Tasks"],
)


@router.post(
    "/{agent_id}/calls/{call_id}/follow-up-tasks",
    response_model=FollowUpTaskResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_task(
    agent_id: int,
    call_id: int,
    task_data: FollowUpTaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not assigned to any organization",
        )

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

    return create_follow_up_task(
        db=db,
        organization_id=current_user.organization_id,
        agent_call_id=call_id,
        task_data=task_data,
    )


@router.get(
    "/{agent_id}/calls/{call_id}/follow-up-tasks",
    response_model=List[FollowUpTaskResponse],
)
def get_tasks(
    agent_id: int,
    call_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not assigned to any organization",
        )

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

    return get_follow_up_tasks_by_call(
        db=db,
        agent_call_id=call_id,
        organization_id=current_user.organization_id,
    )


@router.put(
    "/{agent_id}/calls/{call_id}/follow-up-tasks/{task_id}",
    response_model=FollowUpTaskResponse,
)
def update_task(
    agent_id: int,
    call_id: int,
    task_id: int,
    task_data: FollowUpTaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not assigned to any organization",
        )

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

    task = get_follow_up_task(
        db=db,
        task_id=task_id,
        organization_id=current_user.organization_id,
    )

    if (
        not task
        or task.agent_call_id != call_id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Follow-up task not found",
        )

    return update_follow_up_task(
        db=db,
        task=task,
        task_data=task_data,
        organization_id=current_user.organization_id,
    )
