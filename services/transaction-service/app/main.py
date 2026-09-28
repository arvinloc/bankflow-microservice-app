from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.clients.accounts import accounts_client
from app.routers import transactions
from app.services import IdempotencyConflict, TransactionNotFound


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await accounts_client.close()


app = FastAPI(title="transaction-service", lifespan=lifespan)
app.include_router(transactions.router)


@app.exception_handler(TransactionNotFound)
async def not_found(request: Request, exc: TransactionNotFound):
    return JSONResponse(status_code=404, content={"detail": "Transaction not found"})


@app.exception_handler(IdempotencyConflict)
async def idem_conflict(request: Request, exc: IdempotencyConflict):
    return JSONResponse(status_code=422, content={"detail": "Idempotency-Key reused with a different request"})


@app.get("/health/live", tags=["health"])
async def live():
    return {"status": "ok"}
