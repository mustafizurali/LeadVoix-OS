from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.app.models.organization import Organization
from backend.app.models.user import User
from backend.app.schemas.organization import OrganizationCreate


def create_organization(
    db: Session,
    organization: OrganizationCreate,
    current_user: User,
):
    if current_user.organization_id is not None:
        raise HTTPException(
            status_code=400,
            detail="User already belongs to an organization",
        )

    slug = organization.name.lower().replace(" ", "-")

    existing = (
        db.query(Organization)
        .filter(Organization.slug == slug)
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Organization already exists",
        )

    db_organization = Organization(
        name=organization.name,
        slug=slug,
        plan="free",
    )

    db.add(db_organization)
    db.flush()

    current_user.organization_id = db_organization.id
    current_user.role = "owner"

    db.commit()

    db.refresh(db_organization)
    db.refresh(current_user)

    return db_organization