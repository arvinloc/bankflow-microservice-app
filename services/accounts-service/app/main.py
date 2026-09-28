from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.routers import accounts, internal
from app.services import AccountNotFound, TransferError

app = FastAPI(title="accounts-service")
app.include_router(accounts.router)
app.include_router(internal.router)


@app.exception_handler(TransferError)
async def transfer_error_handler(request: Request, exc: TransferError):
    return JSONResponse(status_code=409, content={"detail": {"code": exc.code}})
@app.exception_handler(AccountNotFound)
async def account_not_found_handler(request: Request, exc: AccountNotFound):
    return JSONResponse(status_code=404, content={"detail": "Account not found"})


@app.get("/health/live", tags=["health"])
async def live():
    return {"status": "ok"}