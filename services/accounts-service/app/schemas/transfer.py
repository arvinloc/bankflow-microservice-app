import uuid
from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.account import Currency


class TransferRequest(BaseModel):
    transaction_id: uuid.UUID
    user_id: uuid.UUID            # владелец счёта-отправителя
    from_account_id: uuid.UUID
    to_account_number: str
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    currency: Currency