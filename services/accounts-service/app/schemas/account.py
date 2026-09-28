import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, ConfigDict

Currency = Literal["EUR","USD","BYN"]

class AccountCreate(BaseModel):
    currency: Currency = "EUR"
    name: str | None = Field(default=None, max_length=50)


class DepositRequest(BaseModel):
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)


class AccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    number: str
    currency: str
    name: str | None
    balance: Decimal
    created_at: datetime


class BalanceOut(BaseModel):
    account_id: uuid.UUID
    balance: Decimal
    currency: str