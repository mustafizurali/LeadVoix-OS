import json
from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from backend.app.models.lead import Lead
from backend.app.models.user import User
from backend.app.models.agent_call import AgentCall
from backend.app.models.company import Company
from backend.app.models.contact import Contact
from backend.app.models.deal import Deal
from backend.app.models.pipeline import Pipeline
from backend.app.models.pipeline_stage import PipelineStage
from backend.app.models.activity import Activity
from backend.app.schemas.company import CompanyResponse
from backend.app.schemas.contact import ContactResponse
from backend.app.schemas.deal import DealResponse
from backend.app.schemas.lead import (
    LeadCreate,
    LeadUpdate,
    LeadConvertRequest,
    LeadConvertResponse,
    LeadResponse,
)
from backend.app.utils.phone import normalize_phone


def create_lead(
    db: Session,
    lead: LeadCreate,
    current_user: User,
):
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=400,
            detail="User is not assigned to any organization"
        )

    phone_normalized, phone_extension = normalize_phone(lead.phone)

    db_lead = Lead(
        first_name=lead.first_name,
        last_name=lead.last_name,
        email=lead.email,
        phone=lead.phone,
        phone_normalized=phone_normalized,
        phone_extension=phone_extension,
        company=lead.company,
        source=lead.source or "manual",
        notes=lead.notes,
        status="new",
        organization_id=current_user.organization_id,
    )

    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)

    return db_lead


def get_leads(
    db: Session,
    current_user: User,
    search: str | None = None,
    status: str | None = None,
    source: str | None = None,
    company: str | None = None,
    page: int = 1,
    limit: int = 10,
    sort_by: str = "created_at",
    order: str = "desc",
):
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=400,
            detail="User is not assigned to any organization"
        )

    query = (
        db.query(Lead)
        .filter(
            Lead.organization_id == current_user.organization_id
        )
    )

    # Search
    if search:
        search = f"%{search}%"
        query = query.filter(
            or_(
                Lead.first_name.ilike(search),
                Lead.last_name.ilike(search),
                Lead.email.ilike(search),
                Lead.phone.ilike(search),
                Lead.company.ilike(search),
            )
        )

    # Filters
    if status:
        query = query.filter(
            Lead.status == status
        )

    if source:
        query = query.filter(
            Lead.source == source
        )

    if company:
        query = query.filter(
            Lead.company.ilike(f"%{company}%")
        )

    allowed_sort_fields = {
        "id": Lead.id,
        "first_name": Lead.first_name,
        "last_name": Lead.last_name,
        "email": Lead.email,
        "company": Lead.company,
        "status": Lead.status,
        "source": Lead.source,
        "created_at": Lead.created_at,
        "updated_at": Lead.updated_at,
    }

    sort_column = allowed_sort_fields.get(
        sort_by,
        Lead.created_at,
    )

    if order.lower() == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    total = query.count()

    leads = (
        query
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return {
        "items": leads,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit,
    }


def update_lead(
    db: Session,
    lead_id: int,
    lead: LeadUpdate,
    current_user: User,
):
    db_lead = (
        db.query(Lead)
        .filter(
            Lead.id == lead_id,
            Lead.organization_id == current_user.organization_id,
        )
        .first()
    )

    if not db_lead:
        raise HTTPException(
            status_code=404,
            detail="Lead not found"
        )

    update_data = lead.model_dump(exclude_unset=True)

    if "phone" in update_data:
        phone_normalized, phone_extension = normalize_phone(update_data["phone"])
        update_data["phone_normalized"] = phone_normalized
        update_data["phone_extension"] = phone_extension

    for key, value in update_data.items():
        setattr(db_lead, key, value)

    db.commit()
    db.refresh(db_lead)

    return db_lead


def delete_lead(
    db: Session,
    lead_id: int,
    current_user: User,
):
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=400,
            detail="User is not assigned to any organization",
        )

    db_lead = (
        db.query(Lead)
        .filter(
            Lead.id == lead_id,
            Lead.organization_id == current_user.organization_id,
        )
        .first()
    )

    if not db_lead:
        raise HTTPException(
            status_code=404,
            detail="Lead not found",
        )

    db.delete(db_lead)
    db.commit()

    return {
        "message": "Lead deleted successfully"
    }


def get_lead_calls(
    db: Session,
    lead_id: int,
    current_user: User,
):
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=400,
            detail="User is not assigned to any organization",
        )

    # Get lead belonging to current user's organization
    lead = (
        db.query(Lead)
        .filter(
            Lead.id == lead_id,
            Lead.organization_id == current_user.organization_id,
        )
        .first()
    )

    if not lead:
        raise HTTPException(
            status_code=404,
            detail="Lead not found",
        )

    # Resolve normalized phone target
    target_norm = lead.phone_normalized
    if not target_norm and lead.phone:
        target_norm, _ = normalize_phone(lead.phone)

    if not target_norm:
        return []

    # Candidates for index seek without guessing country codes
    candidates = [target_norm]
    if target_norm.startswith("+"):
        candidates.append(target_norm.lstrip("+"))
    else:
        candidates.append(f"+{target_norm}")

    # Indexed direct SQL query matching tenant organization_id and caller_phone_normalized
    calls = (
        db.query(AgentCall)
        .filter(
            AgentCall.organization_id == current_user.organization_id,
            AgentCall.caller_phone_normalized.in_(candidates),
        )
        .order_by(AgentCall.created_at.desc())
        .all()
    )

    return calls


def convert_lead(
    db: Session,
    lead_id: int,
    convert_data: LeadConvertRequest,
    current_user: User,
) -> LeadConvertResponse:
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=400,
            detail="User is not assigned to any organization",
        )

    try:
        # 1. Validate Lead exists and belongs to current_user.organization_id
        lead = (
            db.query(Lead)
            .filter(
                Lead.id == lead_id,
                Lead.organization_id == current_user.organization_id,
            )
            .first()
        )
        if not lead:
            raise HTTPException(
                status_code=404,
                detail="Lead not found",
            )

        # 2. Reject already-converted Leads with HTTP 409
        if lead.status and lead.status.lower() == "converted":
            raise HTTPException(
                status_code=409,
                detail="Lead has already been converted",
            )

        # 3. Reject duplicate Contact conversion, including existing Contact linked through lead_id
        existing_linked = (
            db.query(Contact)
            .filter(
                Contact.lead_id == lead.id,
                Contact.organization_id == current_user.organization_id,
            )
            .first()
        )
        if existing_linked:
            raise HTTPException(
                status_code=409,
                detail=f"Lead is already linked to Contact #{existing_linked.id}",
            )

        # 4 & 5. Contact resolution
        contact = None
        if convert_data.contact_id is not None:
            # Validate explicit contact_id belongs to the same organization
            contact = (
                db.query(Contact)
                .filter(
                    Contact.id == convert_data.contact_id,
                    Contact.organization_id == current_user.organization_id,
                )
                .first()
            )
            if not contact:
                raise HTTPException(
                    status_code=404,
                    detail="Specified contact not found in organization",
                )
            # Prevent linking a Contact already associated with another Lead
            if contact.lead_id is not None and contact.lead_id != lead.id:
                raise HTTPException(
                    status_code=409,
                    detail=f"Contact #{contact.id} is already linked to another Lead (#{contact.lead_id})",
                )
            contact.lead_id = lead.id
        else:
            # 6 & 7. Detect duplicate email or normalized phone within the same organization
            lead_phone_norm = lead.phone_normalized
            lead_phone_ext = lead.phone_extension
            if not lead_phone_norm and lead.phone:
                lead_phone_norm, lead_phone_ext = normalize_phone(lead.phone)

            dup_conditions = []
            if lead.email and lead.email.strip():
                dup_conditions.append(Contact.email.ilike(lead.email.strip()))
            if lead_phone_norm:
                dup_conditions.append(Contact.phone_normalized == lead_phone_norm)

            existing_dup = None
            if dup_conditions:
                existing_dup = (
                    db.query(Contact)
                    .filter(
                        Contact.organization_id == current_user.organization_id,
                        or_(*dup_conditions),
                    )
                    .first()
                )

            if existing_dup and not convert_data.create_new_contact_if_exists:
                dup_reason = "email" if (lead.email and existing_dup.email and existing_dup.email.lower() == lead.email.lower()) else "phone"
                raise HTTPException(
                    status_code=409,
                    detail=(
                        f"A contact with matching {dup_reason} already exists (Contact #{existing_dup.id}). "
                        f"Pass contact_id={existing_dup.id} to link, or set create_new_contact_if_exists=true."
                    ),
                )

            contact = Contact(
                first_name=lead.first_name,
                last_name=lead.last_name,
                email=lead.email,
                phone=lead.phone,
                phone_normalized=lead_phone_norm,
                phone_extension=lead_phone_ext,
                company=lead.company,
                company_id=None,
                lead_id=lead.id,
                owner_id=lead.owner_id or current_user.id,
                status="active",
                organization_id=current_user.organization_id,
            )
            db.add(contact)
            db.flush()

        # 8. Resolve Company according to approved design
        resolved_company = None
        if convert_data.company_id is not None:
            resolved_company = (
                db.query(Company)
                .filter(
                    Company.id == convert_data.company_id,
                    Company.organization_id == current_user.organization_id,
                )
                .first()
            )
            if not resolved_company:
                raise HTTPException(
                    status_code=404,
                    detail="Company not found in organization",
                )
        elif lead.company_id is not None:
            resolved_company = (
                db.query(Company)
                .filter(
                    Company.id == lead.company_id,
                    Company.organization_id == current_user.organization_id,
                )
                .first()
            )

        if not resolved_company:
            candidate_name = (convert_data.company_name or lead.company or "").strip()
            if candidate_name:
                matches = (
                    db.query(Company)
                    .filter(
                        Company.organization_id == current_user.organization_id,
                        func.lower(func.trim(Company.name)) == candidate_name.lower(),
                    )
                    .all()
                )
                if len(matches) == 1:
                    resolved_company = matches[0]
                elif len(matches) > 1:
                    raise HTTPException(
                        status_code=409,
                        detail=f"Ambiguous company match: multiple companies found matching '{candidate_name}'. Please specify an explicit company_id.",
                    )
                else:
                    if convert_data.create_company_if_missing:
                        resolved_company = Company(
                            name=candidate_name,
                            organization_id=current_user.organization_id,
                            status="active",
                        )
                        db.add(resolved_company)
                        db.flush()

        if resolved_company:
            contact.company_id = resolved_company.id
            lead.company_id = resolved_company.id

        # 9. Optional Deal creation
        deal = None
        if convert_data.deal_data is not None:
            deal_in = convert_data.deal_data

            pipeline = (
                db.query(Pipeline)
                .filter(
                    Pipeline.id == deal_in.pipeline_id,
                    Pipeline.organization_id == current_user.organization_id,
                )
                .first()
            )
            if not pipeline:
                raise HTTPException(
                    status_code=404,
                    detail="Pipeline not found in organization",
                )

            stage = (
                db.query(PipelineStage)
                .filter(
                    PipelineStage.id == deal_in.stage_id,
                    PipelineStage.pipeline_id == deal_in.pipeline_id,
                )
                .first()
            )
            if not stage:
                raise HTTPException(
                    status_code=400,
                    detail="Stage not found or does not belong to the selected pipeline",
                )

            deal_status = "OPEN"
            if stage.stage_type == "WON":
                deal_status = "WON"
            elif stage.stage_type == "LOST":
                deal_status = "LOST"

            deal_owner_id = deal_in.owner_id or current_user.id
            if deal_in.owner_id is not None:
                owner = (
                    db.query(User)
                    .filter(
                        User.id == deal_in.owner_id,
                        User.organization_id == current_user.organization_id,
                    )
                    .first()
                )
                if not owner:
                    raise HTTPException(
                        status_code=404,
                        detail="Deal owner not found in organization",
                    )

            deal_title = deal_in.title or f"Deal - {lead.first_name} {lead.last_name or ''}".strip()
            deal = Deal(
                title=deal_title,
                amount=deal_in.amount if deal_in.amount is not None else Decimal("0.00"),
                currency=deal_in.currency or "USD",
                status=deal_status,
                expected_close_date=deal_in.expected_close_date,
                description=deal_in.description,
                pipeline_id=pipeline.id,
                stage_id=stage.id,
                lead_id=lead.id,
                contact_id=contact.id,
                company_id=resolved_company.id if resolved_company else None,
                owner_id=deal_owner_id,
                organization_id=current_user.organization_id,
            )
            db.add(deal)
            db.flush()

        # 10. Update Lead status to converted
        lead.status = "converted"

        # 11. Create Activity for the conversion
        lead_full_name = f"{lead.first_name} {lead.last_name or ''}".strip()
        activity_content = f"Converted to Contact #{contact.id}"
        if resolved_company:
            activity_content += f", Company '{resolved_company.name}'"
        if deal:
            activity_content += f", and Deal #{deal.id} ('{deal.title}')"

        meta = {
            "converted_by_user_id": current_user.id,
            "contact_id": contact.id,
            "company_id": resolved_company.id if resolved_company else None,
            "deal_id": deal.id if deal else None,
        }

        conversion_activity = Activity(
            organization_id=current_user.organization_id,
            activity_type="lead_converted",
            title=f"Lead converted: {lead_full_name}",
            content=activity_content,
            metadata_json=json.dumps(meta),
            lead_id=lead.id,
            contact_id=contact.id,
            deal_id=deal.id if deal else None,
            user_id=current_user.id,
        )
        db.add(conversion_activity)
        db.flush()

        # 12 & 13. Exactly one final commit
        db.commit()
        db.refresh(lead)
        db.refresh(contact)
        if resolved_company:
            db.refresh(resolved_company)
        if deal:
            db.refresh(deal)

        return LeadConvertResponse(
            success=True,
            lead=LeadResponse.model_validate(lead),
            contact=ContactResponse.model_validate(contact),
            company=CompanyResponse.model_validate(resolved_company) if resolved_company else None,
            deal=DealResponse.model_validate(deal) if deal else None,
            activity_id=conversion_activity.id,
        )

    except Exception:
        db.rollback()
        raise
