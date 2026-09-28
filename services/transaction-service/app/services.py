import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.accounts import AccountsUnavailable, TransferRejected, accounts_client
from app.models import Transaction, TxStatus
from app.schemas.transactions import TransferCreate, TransferCreate


class TransactionNotFound(Exception):
    pass


class IdempotencyConflict(Exception):
    pass


async def _find_by_key(db: AsyncSession, user_id: uuid.UUID, key: str) -> Transaction | None:
    return await db.scalar(
        select(Transaction).where(Transaction.user_id ==
                                  user_id, Transaction.idempotency_key == key)
    )


async def create_transfer(db: AsyncSession, user_id: uuid.UUID, key: str, data: TransferCreate) -> Transaction:
    tx = await _find_by_key(db, user_id, key)

    if tx is None:
        tx = Transaction(
            user_id=user_id, idempotency_key=key, from_account_id=data.from_account_id,
            to_account_number=data.to_account_number, amount=data.amount, currency=data.currency,
        )
    db.add(tx)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()

        tx = await _find_by_key(db, user_id, key)
    else:
        await db.refresh(tx)

    same_request = (
        tx.from_account_id == data.from_account_id
        and tx.to_account_number == data.to_account_number
        and tx.amount == data.amount
        and tx.currency == data.currency
    )
    if not same_request:
        raise IdempotencyConflict  # тот же ключ, но другое тело запроса

    if tx.status == TxStatus.PENDING:
        await _process(db, tx)
    return tx


async def _process(db: AsyncSession, tx: Transaction) -> None:
    try:
        await accounts_client.apply_transfer(tx)
    except TransferRejected as exc:
        tx.status = TxStatus.FAILED
        tx.failure_reason = exc.code
    except AccountsUnavailable:
        return  # исход неизвестен: остаётся PENDING, клиент может повторить с тем же ключом
    else:
        tx.status = TxStatus.COMPLETED
    await db.commit()
    await db.refresh(tx)


async def get_transaction(db: AsyncSession, tx_id: uuid.UUID, user_id: uuid.UUID) -> Transaction:
    tx = await db.scalar(select(Transaction).where(Transaction.id == tx_id, Transaction.user_id == user_id))
    if tx is None:
        raise TransactionNotFound
    return tx


async def list_transactions(db: AsyncSession, user_id: uuid.UUID, limit: int = 50) -> list[Transaction]:
    result = await db.scalars(
        select(Transaction).where(Transaction.user_id == user_id)
        .order_by(Transaction.created_at.desc()).limit(limit)
    )
    return list(result)
