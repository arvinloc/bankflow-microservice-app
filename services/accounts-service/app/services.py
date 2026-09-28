import secrets
import string
import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .models import Account, LedgerEntry


class AccountNotFound(Exception):
    pass

def _generate_number() -> str:
    return "".join(secrets.choice(string.digits) for _ in range(16))


async def open_account(db: AsyncSession, owner_id: uuid.UUID, currency: str, name: str | None) -> Account:
    account = Account(owner_id=owner_id, number=_generate_number(), currency=currency, name=name)
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


async def list_accounts(db: AsyncSession, owner_id: uuid.UUID) -> list[Account]:
    result = await db.scalars(
        select(Account).where(Account.owner_id == owner_id).order_by(Account.created_at)
    )
    return list(result)

async def get_account(
    db: AsyncSession, account_id: uuid.UUID, owner_id: uuid.UUID, *, for_update: bool = False
) -> Account:

    stmt = select(Account).where(Account.id == account_id, Account.owner_id == owner_id)
    if for_update:
        stmt = stmt.with_for_update()  # блокируем строку, чтобы два пополнения не затёрли друг друга
    account = await db.scalar(stmt)
    if account is None:
        raise AccountNotFound
    return account

async def deposit(db: AsyncSession, account_id: uuid.UUID, owner_id: uuid.UUID, amount: Decimal) -> Account:
    account = await get_account(db, account_id, owner_id, for_update=True)
    account.balance += amount
    await db.commit()
    await db.refresh(account)
    return account


class TransferError(Exception):
    def __init__(self, code: str):
        self.code = code


async def apply_transfer(
    db: AsyncSession, *, transaction_id: uuid.UUID, user_id: uuid.UUID,
    from_account_id: uuid.UUID, to_account_number: str, amount: Decimal, currency: str,
) -> None:
    recipient_id = await db.scalar(select(Account.id).where(Account.number == to_account_number))
    if recipient_id is None:
        raise TransferError("RECIPIENT_NOT_FOUND")
    if recipient_id == from_account_id:
        raise TransferError("SAME_ACCOUNT")

    # Блокируем ОБА счёта в одном порядке (по id). Иначе два встречных перевода
    # A→B и B→A могут заблокировать друг друга (deadlock).
    rows = await db.scalars(
        select(Account)
        .where(Account.id.in_([from_account_id, recipient_id]))
        .order_by(Account.id)
        .with_for_update()
    )
    accounts = {a.id: a for a in rows}
    sender = accounts.get(from_account_id)
    if sender is None or sender.owner_id != user_id:
        raise TransferError("ACCOUNT_NOT_FOUND")
    recipient = accounts[recipient_id]

    # Идемпотентность: проверяем ПОСЛЕ блокировки, чтобы параллельные дубли не проскочили
    already = await db.scalar(
        select(LedgerEntry.id).where(LedgerEntry.transaction_id == transaction_id).limit(1)
    )
    if already:
        return

    if sender.currency != currency or recipient.currency != currency:
        raise TransferError("CURRENCY_MISMATCH")
    if sender.balance < amount:
        raise TransferError("INSUFFICIENT_FUNDS")

    sender.balance -= amount
    recipient.balance += amount
    db.add_all([
        LedgerEntry(account_id=sender.id, transaction_id=transaction_id, amount=-amount),
        LedgerEntry(account_id=recipient.id, transaction_id=transaction_id, amount=amount),
    ])
    await db.commit()  # дебет, кредит и журнал: всё или ничего