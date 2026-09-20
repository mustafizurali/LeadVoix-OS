from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class SubscriptionCreate(BaseModel):
    organization_id: int
    provider: str = "razorpay"
    provider_subscription_id: Optional[str] = None
    plan: str
    status: str = "created"
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool = False


class SubscriptionResponse(BaseModel):
    id: int
    organization_id: int
    provider: str
    provider_subscription_id: Optional[str]
    plan: str
    status: str
    current_period_start: Optional[datetime]
    current_period_end: Optional[datetime]
    cancel_at_period_end: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)