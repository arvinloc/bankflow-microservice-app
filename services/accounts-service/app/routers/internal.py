from fastapi import APIRouter

from app import services
from app.dependencies import DbSession, ServiceDep
from app.schemas.transfer import TransferRequest

router = APIRouter(prefix="/internal", tags=["internal"])


@router.post("/transfers")
async def apply_transfer(body: TransferRequest, db: DbSession, _: ServiceDep):
    await services.apply_transfer(db, **body.model_dump())
    return {"status": "APPLIED"}