from fastapi import APIRouter
from .payments import router as router_payments

router = APIRouter()

router.include_router(router_payments)
