from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from backend.app.schemas.company import CompanyResponse
from backend.app.schemas.contact import ContactResponse
from backend.app.schemas.deal import DealResponse


class LeadCreate(BaseModel):
    first_name: str
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    source: Optional[str] = None
    notes: Optional[str] = None


class LeadResponse(BaseModel):
    id: int
    first_name: str
    last_name: Optional[str]
    email: Optional[EmailStr]
    phone: Optional[str]
    phone_normalized: Optional[str] = None
    phone_extension: Optional[str] = None
    company: Optional[str]
    company_id: Optional[int] = None
    owner_id: Optional[int] = None
    source: Optional[str]
    notes: Optional[str]
    status: str
    organization_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LeadUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    source: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None


class DealCreateForConversion(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    amount: Decimal = Decimal("0.00")
    currency: str = "USD"
    pipeline_id: int
    stage_id: int
    expected_close_date: Optional[date] = None
    description: Optional[str] = None
    owner_id: Optional[int] = None


class LeadConvertRequest(BaseModel):
    contact_id: Optional[int] = None
    create_new_contact_if_exists: bool = False
    company_id: Optional[int] = None
    company_name: Optional[str] = None
    create_company_if_missing: bool = True
    deal_data: Optional[DealCreateForConversion] = None


class LeadConvertResponse(BaseModel):
    success: bool = True
    lead: LeadResponse
    contact: ContactResponse
    company: Optional[CompanyResponse] = None
    deal: Optional[DealResponse] = None
    activity_id: int

    model_config = ConfigDict(from_attributes=True)
