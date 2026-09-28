import uuid

from fastapi import APIRouter, status

from app import services
from app.dependencies import DbSession, UserDep
from app.schemas.account import AccountCreate, AccountOut, BalanceOut, DepositRequest

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post("/", response_model=AccountOut, status_code=status.HTTP_201_CREATED)
async def create_account(body: AccountCreate, db: DbSession, user: UserDep):
    return await services.open_account(db, user.id, body.currency, body.name)


@router.get("/", response_model=list[AccountOut])
async def my_accounts(db: DbSession, user: UserDep):
    return await services.list_accounts(db, user.id)


@router.get("/{account_id}", response_model=AccountOut)
async def get_account(account_id: uuid.UUID, db: DbSession, user: UserDep):
    return await services.get_account(db, account_id, user.id)


@router.get("/{account_id}/balance", response_model=BalanceOut)
async def get_balance(account_id: uuid.UUID, db: DbSession, user: UserDep):
    account = await services.get_account(db, account_id, user.id)
    return BalanceOut(account_id=account.id, balance=account.balance, currency=account.currency)


@router.post("/{account_id}/deposit", response_model=AccountOut)
async def deposit(account_id: uuid.UUID, body: DepositRequest, db: DbSession, user: UserDep):
    return await services.deposit(db, account_id, user.id, body.amount)