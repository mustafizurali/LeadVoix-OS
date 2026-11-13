from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from backend.app.models.organization import Organization

from backend.app.models.user import User
from backend.app.schemas.user import UserCreate
from backend.app.utils.security import (
    hash_password,
    verify_password,
)


def canonicalize_email(email: str) -> str:
    return str(email).strip().lower()


def get_users_by_canonical_email(db: Session, email: str):
    canonical_email = canonicalize_email(email)
    return (
        db.query(User)
        .filter(func.lower(func.trim(User.email)) == canonical_email)
        .all()
    )


def create_user(db: Session, user: UserCreate):
    canonical_email = canonicalize_email(user.email)
    existing_users = get_users_by_canonical_email(db, canonical_email)

    if existing_users:
        raise HTTPException(
            status_code=400,
            detail="Email already registered",
        )

    # Create user first
    db_user = User(
        name=user.name,
        email=canonical_email,
        hashed_password=hash_password(user.password),
        role="owner",
    )

    db.add(db_user)
    db.flush()

    # Create a personal organization for the new user
    db_organization = Organization(
        name=f"{user.name}'s Organization",
        slug=f"org-{db_user.id}",
        plan="free",
    )

    db.add(db_organization)
    db.flush()

    # Assign organization to user
    db_user.organization_id = db_organization.id

    db.commit()
    db.refresh(db_user)

    return db_user


def authenticate_user(
    db: Session,
    email: str,
    password: str,
):
    users = get_users_by_canonical_email(db, email)

    if len(users) != 1:
        return None

    user = users[0]

    result = verify_password(
        password,
        user.hashed_password,
    )

    if not result:
        return None

    return user
