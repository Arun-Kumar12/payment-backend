from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class PaymentSchema(BaseModel):
    id: Optional[str]
    payee_first_name: str
    payee_last_name: str
    payee_payment_status: str
    payee_added_date_utc: datetime
    payee_due_date: datetime
    total_due: float

    class Config:
        orm_mode = True
