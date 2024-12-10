from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import date, datetime

class Payment(BaseModel):
    payee_first_name: str
    payee_last_name: str
    payee_payment_status: str
    payee_added_date_utc: datetime
    payee_due_date: date
    payee_address_line_1: str
    payee_address_line_2: Optional[str]
    payee_city: str
    payee_country: str
    payee_province_or_state: Optional[str]
    payee_postal_code: str
    payee_phone_number: str
    payee_email: EmailStr
    currency: str
    discount_percent: Optional[float]
    tax_percent: Optional[float]
    due_amount: float
    evidence_id:Optional[str] = None
