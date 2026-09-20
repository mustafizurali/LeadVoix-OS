from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.db.database import get_db
from backend.app.models.subscription import Subscription
from backend.app.models.user import User
from backend.app.services.subscription import create_razorpay_subscription
from backend.app.utils.dependencies import get_current_user


router = APIRouter(
    prefix="/subscriptions",
    tags=["Subscriptions"],
)


@router.post("/create")
def create_subscription(
    plan: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    organization_id = current_user.organization_id

    if not organization_id:
        raise HTTPException(
            status_code=400,
            detail="User is not associated with an organization",
        )

    allowed_plans = {"starter", "growth", "scale"}

    normalized_plan = plan.lower().strip()

    if normalized_plan not in allowed_plans:
        raise HTTPException(
            status_code=400,
            detail="Invalid subscription plan",
        )

    try:
        razorpay_subscription = create_razorpay_subscription(
            plan=normalized_plan,
            total_count=12,
            customer_notify=True,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )
    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Failed to create Razorpay subscription",
        )

    subscription = Subscription(
        organization_id=organization_id,
        provider="razorpay",
        provider_subscription_id=razorpay_subscription.get("id"),
        plan=normalized_plan,
        status=razorpay_subscription.get("status", "created"),
        cancel_at_period_end=False,
    )

    db.add(subscription)
    db.commit()
    db.refresh(subscription)

    return {
        "subscription_id": subscription.id,
        "razorpay_subscription_id": subscription.provider_subscription_id,
        "plan": subscription.plan,
        "status": subscription.status,
    }