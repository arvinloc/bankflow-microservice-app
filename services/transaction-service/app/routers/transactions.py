import uuid
from typing import Annotated

from fastapi import APIRouter, Header, Response

from app import services
from app.dependencies import DbSession, UserDep
from app.models import TxStatus
from app.schemas.transactions import TransactionOut, TransferCreate

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("", response_model=TransactionOut, status_code=201)
async def create_transaction(
    body: TransferCreate,
    response: Response,
    db: DbSession,
    user: UserDep,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=64)],
):
    tx = await services.create_transfer(db, user.id, idempotency_key, body)
    if tx.status == TxStatus.PENDING:
        response.status_code = 202
    return tx


@router.get("", response_model=list[TransactionOut])
async def my_transactions(db: DbSession, user: UserDep):
    return await services.list_transactions(db, user.id)


@router.get("/{transaction_id}", response_model=TransactionOut)
async def get_transaction(transaction_id: uuid.UUID, db: DbSession, user: UserDep):
    return await services.get_transaction(db, transaction_id, user.id)
