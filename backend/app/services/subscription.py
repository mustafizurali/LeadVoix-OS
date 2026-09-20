import os
import httpx


RAZORPAY_BASE_URL = "https://api.razorpay.com/v1"


def get_razorpay_credentials():
    key_id = os.getenv("RAZORPAY_KEY_ID", "").strip()
    key_secret = os.getenv("RAZORPAY_KEY_SECRET", "").strip()

    if not key_id or not key_secret:
        raise ValueError("Razorpay credentials are not configured")

    return key_id, key_secret


def get_razorpay_plan_id(plan: str):
    plan_map = {
        "starter": os.getenv("RAZORPAY_STARTER_PLAN_ID", "").strip(),
        "growth": os.getenv("RAZORPAY_GROWTH_PLAN_ID", "").strip(),
        "scale": os.getenv("RAZORPAY_SCALE_PLAN_ID", "").strip(),
    }

    plan_id = plan_map.get(plan.lower().strip())

    if not plan_id:
        raise ValueError(f"Razorpay plan is not configured for: {plan}")

    return plan_id


def create_razorpay_subscription(
    plan: str,
    total_count: int = 12,
    customer_notify: bool = True,
):
    key_id, key_secret = get_razorpay_credentials()
    razorpay_plan_id = get_razorpay_plan_id(plan)

    payload = {
        "plan_id": razorpay_plan_id,
        "total_count": total_count,
        "customer_notify": 1 if customer_notify else 0,
    }

    response = httpx.post(
        f"{RAZORPAY_BASE_URL}/subscriptions",
        json=payload,
        auth=(key_id, key_secret),
        timeout=30.0,
    )

    response.raise_for_status()

    return response.json()