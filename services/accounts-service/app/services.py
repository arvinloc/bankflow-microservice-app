import secrets
import string
import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .models import Account

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