import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, String, Uuid, Numeric, DateTime, func, UniqueConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base



class Account(Base):
    __tablename__ = "accounts"

    __table_args__ = (
        CheckConstraint("balance >= 0", name="ck_accounts_balance_non_negative"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True)  # sub из токена Keycloak
    number: Mapped[str] = mapped_column(String(20), unique=True)
    currency: Mapped[str] = mapped_column(String(3))
    name: Mapped[str | None] = mapped_column(String(50))
    balance: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0.00"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LedgerEntry(Base):
    """Журнал движений. amount: плюс = зачисление, минус = списание."""
    __tablename__ = "ledger_entries"
    __table_args__ = (UniqueConstraint("account_id", "transaction_id"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("accounts.id"), index=True)
    transaction_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())