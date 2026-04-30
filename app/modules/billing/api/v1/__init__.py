from fastapi import APIRouter
from .endpoints.invoice import router as invoice_router
from .endpoints.billing_item import router as billing_item_router
from .endpoints.payment import router as payment_router

router = APIRouter()
router.include_router(invoice_router, prefix="/invoices", tags=["Invoices"])
router.include_router(billing_item_router, prefix="/billing-items", tags=["Billing Items"])
router.include_router(payment_router, prefix="/payments", tags=["Payments"])