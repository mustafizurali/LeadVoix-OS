from math import ceil
from sqlalchemy import or_
from sqlalchemy.orm import Session
from fastapi import HTTPException

from backend.app.models.company import Company
from backend.app.models.contact import Contact
from backend.app.models.user import User
from backend.app.schemas.contact import ContactCreate, ContactUpdate
from backend.app.utils.phone import normalize_phone


def create_contact(
    db: Session,
    contact: ContactCreate,
    current_user: User,
):
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=400,
            detail="User is not assigned to any organization",
        )

    # Validate company_id if provided
    if contact.company_id is not None:
        company = (
            db.query(Company)
            .filter(
                Company.id == contact.company_id,
                Company.organization_id == current_user.organization_id,
            )
            .first()
        )
        if not company:
            raise HTTPException(
                status_code=404,
                detail="Company not found",
            )

    # Normalize phone
    phone_normalized, phone_extension = normalize_phone(contact.phone)

    db_contact = Contact(
        first_name=contact.first_name,
        last_name=contact.last_name,
        email=contact.email,
        phone=contact.phone,
        phone_normalized=phone_normalized,
        phone_extension=phone_extension,
        company=contact.company,
        company_id=contact.company_id,
        status="new",
        organization_id=current_user.organization_id,
    )

    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)

    return db_contact


def get_contacts(
    db: Session,
    current_user: User,
    page: int = 1,
    limit: int = 10,
    search: str | None = None,
):
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=400,
            detail="User is not assigned to any organization",
        )

    query = db.query(Contact).filter(
        Contact.organization_id == current_user.organization_id
    )

    if search:
        query = query.filter(
            or_(
                Contact.first_name.ilike(f"%{search}%"),
                Contact.last_name.ilike(f"%{search}%"),
                Contact.email.ilike(f"%{search}%"),
                Contact.phone.ilike(f"%{search}%"),
                Contact.company.ilike(f"%{search}%"),
            )
        )

    total = query.count()

    contacts = (
        query
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    total_pages = ceil(total / limit) if total > 0 else 1

    return {
        "items": contacts,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
    }


def get_company_contacts(
    db: Session,
    company_id: int,
    current_user: User,
    page: int = 1,
    limit: int = 10,
):
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=400,
            detail="User is not assigned to any organization",
        )

    # Validate company belongs to authenticated user's organization
    company = (
        db.query(Company)
        .filter(
            Company.id == company_id,
            Company.organization_id == current_user.organization_id,
        )
        .first()
    )

    if not company:
        raise HTTPException(
            status_code=404,
            detail="Company not found",
        )

    query = (
        db.query(Contact)
        .filter(
            Contact.company_id == company_id,
            Contact.organization_id == current_user.organization_id,
        )
        .order_by(Contact.created_at.desc())
    )

    total = query.count()

    contacts = (
        query
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    total_pages = ceil(total / limit) if total > 0 else 1

    return {
        "items": contacts,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
    }


def update_contact(
    db: Session,
    contact_id: int,
    contact: ContactUpdate,
    current_user: User,
):
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=400,
            detail="User is not assigned to any organization",
        )

    db_contact = (
        db.query(Contact)
        .filter(
            Contact.id == contact_id,
            Contact.organization_id == current_user.organization_id,
        )
        .first()
    )

    if not db_contact:
        raise HTTPException(
            status_code=404,
            detail="Contact not found",
        )

    update_data = contact.model_dump(exclude_unset=True)

    # Validate company_id if provided in update
    if "company_id" in update_data and update_data["company_id"] is not None:
        company = (
            db.query(Company)
            .filter(
                Company.id == update_data["company_id"],
                Company.organization_id == current_user.organization_id,
            )
            .first()
        )
        if not company:
            raise HTTPException(
                status_code=404,
                detail="Company not found",
            )

    # Update normalized phone if phone is updated
    if "phone" in update_data:
        phone_normalized, phone_extension = normalize_phone(update_data["phone"])
        update_data["phone_normalized"] = phone_normalized
        update_data["phone_extension"] = phone_extension

    for key, value in update_data.items():
        setattr(db_contact, key, value)

    db.commit()
    db.refresh(db_contact)

    return db_contact


def delete_contact(
    db: Session,
    contact_id: int,
    current_user: User,
):
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=400,
            detail="User is not assigned to any organization",
        )

    db_contact = (
        db.query(Contact)
        .filter(
            Contact.id == contact_id,
            Contact.organization_id == current_user.organization_id,
        )
        .first()
    )

    if not db_contact:
        raise HTTPException(
            status_code=404,
            detail="Contact not found",
        )

    db.delete(db_contact)
    db.commit()

    return {
        "message": "Contact deleted successfully"
    }
