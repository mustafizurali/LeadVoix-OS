import os

import resend
from sqlalchemy.orm import Session

from backend.app.models.demo_request import DemoRequest
from backend.app.schemas.demo_request import DemoRequestCreate


def create_demo_request(
    db: Session,
    demo_request: DemoRequestCreate,
):
    db_demo_request = DemoRequest(
        name=demo_request.name,
        email=demo_request.email,
        company=demo_request.company,
        phone=demo_request.phone,
        message=demo_request.message,
        status="new",
    )

    db.add(db_demo_request)
    db.commit()
    db.refresh(db_demo_request)

    # Send admin notification email
    try:
        resend_api_key = os.getenv("RESEND_API_KEY", "").strip()

        # Remove Bearer prefix if accidentally included in Render
        if resend_api_key.lower().startswith("bearer "):
            resend_api_key = resend_api_key[7:].strip()

        resend.api_key = resend_api_key

        admin_email = os.getenv("ADMIN_EMAIL", "").strip()

        from_email = os.getenv(
            "RESEND_FROM_EMAIL",
            "hello@leadvoix.com",
        ).strip()

        resend.Emails.send(
            {
                "from": from_email,
                "to": [admin_email],
                "subject": "New Demo Request - LeadVoix AI",
                "html": f"""
                    <h2>New Demo Request</h2>

                    <p><strong>Name:</strong> {demo_request.name}</p>
                    <p><strong>Email:</strong> {demo_request.email}</p>
                    <p><strong>Company:</strong> {demo_request.company}</p>
                    <p><strong>Phone:</strong> {demo_request.phone or "Not provided"}</p>
                    <p><strong>Message:</strong> {demo_request.message or "No message"}</p>

                    <hr>

                    <p>
                        This demo request was submitted from
                        <strong>LeadVoix AI</strong>.
                    </p>
                """,
            }
        )

        print("Demo request email notification sent successfully.")

    except Exception as error:
        # Email failure must not break demo request submission
        print(f"Demo request email notification failed: {error}")

    return db_demo_request


def get_demo_requests(
    db: Session,
):
    return (
        db.query(DemoRequest)
        .order_by(DemoRequest.created_at.desc())
        .all()
    )


def update_demo_request_status(
    db: Session,
    demo_request: DemoRequest,
    status: str,
):
    demo_request.status = status

    db.commit()
    db.refresh(demo_request)

    return demo_request