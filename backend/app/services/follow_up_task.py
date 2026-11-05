from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.app.models.follow_up_task import (
    FollowUpTask,
)
from backend.app.schemas.follow_up_task import (
    FollowUpTaskCreate,
    FollowUpTaskUpdate,
)


def create_follow_up_task(
    db: Session,
    organization_id: int,
    agent_call_id: int,
    task_data: FollowUpTaskCreate,
) -> FollowUpTask:
    # Organization ID is strictly derived from authenticated context, never client payload
    data = task_data.model_dump(exclude={"organization_id", "agent_call_id"})

    task = FollowUpTask(
        organization_id=organization_id,
        agent_call_id=agent_call_id,
        **data,
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    return task


def get_follow_up_task(
    db: Session,
    task_id: int,
    organization_id: int,
) -> Optional[FollowUpTask]:
    return (
        db.query(FollowUpTask)
        .filter(
            FollowUpTask.id == task_id,
            FollowUpTask.organization_id == organization_id,
        )
        .first()
    )


def get_follow_up_tasks_by_call(
    db: Session,
    agent_call_id: int,
    organization_id: int,
) -> List[FollowUpTask]:
    return (
        db.query(FollowUpTask)
        .filter(
            FollowUpTask.agent_call_id == agent_call_id,
            FollowUpTask.organization_id == organization_id,
        )
        .order_by(
            FollowUpTask.created_at.desc()
        )
        .all()
    )


def get_pending_follow_up_task(
    db: Session,
    agent_call_id: int,
    organization_id: int,
) -> Optional[FollowUpTask]:
    return (
        db.query(FollowUpTask)
        .filter(
            FollowUpTask.agent_call_id == agent_call_id,
            FollowUpTask.organization_id == organization_id,
            FollowUpTask.is_completed == False,
        )
        .first()
    )


def update_follow_up_task(
    db: Session,
    task: FollowUpTask,
    task_data: FollowUpTaskUpdate,
    organization_id: int,
) -> FollowUpTask:
    if task.organization_id != organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Follow-up task not found",
        )

    # Exclude immutable or security-critical fields from client payload
    update_data = task_data.model_dump(
        exclude_unset=True,
        exclude={"organization_id", "agent_call_id"},
    )

    for field, value in update_data.items():
        setattr(
            task,
            field,
            value,
        )

    if (
        task.is_completed
        and task.completed_at is None
    ):
        task.completed_at = datetime.now(
            timezone.utc
        )

    db.commit()
    db.refresh(task)

    return task
