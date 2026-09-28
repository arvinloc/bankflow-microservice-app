import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Currency = Literal["EUR", "USD", "BYN"]


class TransferCreate(BaseModel):
    from_account_id: uuid.UUID
    to_account_number: str = Field(pattern=r"^\d{16}$")
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    currency: Currency = "BYN"


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    from_account_id: uuid.UUID
    to_account_number: str
    amount: Decimal
    currency: str
    status: str
    failure_reason: str | None
    created_at: datetime
