from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Annotated
from datetime import date

class PaymentModel(BaseModel):
    payee_first_name: str
    payee_last_name: str
    payee_payment_status: Annotated[
        str, 
        Field(pattern=r"^(completed|due_now|overdue|pending)$")
    ]
    payee_added_date_utc: int
    payee_due_date: str
    payee_address_line_1: str
    payee_address_line_2: Optional[str]
    payee_city: str
    payee_country: Annotated[str, Field(pattern=r"^[A-Z]{2}$")]
    payee_province_or_state: Optional[str]
    payee_postal_code: str
    payee_phone_number: Annotated[str, Field(pattern=r"^\+\d{1,15}$")]
    payee_email: EmailStr
    currency: Annotated[str, Field(pattern=r"^[A-Z]{3}$")]
    discount_percent: Optional[float] = 0.0
    tax_percent: Optional[float] = 0.0
    due_amount: float
    evidence_file_path: Optional[str] = None
