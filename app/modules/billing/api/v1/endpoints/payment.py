# app/modules/billing/payment_api.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.api.db import get_db
from app.common.dependencies.auth import get_current_user, require_role
from app.common.exceptions.billing import InvoiceNotFoundError, OverpaymentError, PaymentNotFoundError
from app.modules.billing.enums.base import PaymentMethod
from app.modules.billing.schemas.base import PaymentCreate, PaymentResponse, PaymentUpdate
from app.modules.billing.services.payment import PaymentService
from app.modules.user.models.base import User


router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    data: PaymentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("receptionist")),
):
    service = PaymentService(db)
    try:
        payment = await service.create_payment(data)
        return payment
    except InvoiceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except OverpaymentError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[PaymentResponse])
async def list_payments(
    invoice_id: Optional[int] = Query(None),
    method: Optional[PaymentMethod] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    filters = {}
    if invoice_id:
        filters["invoice_id"] = invoice_id
    if method:
        filters["method"] = method
    # date filtering could be added
    service = PaymentService(db)
    payments = await service.get_payments(filters=filters, skip=skip, limit=limit)
    return payments


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = PaymentService(db)
    payment = await service.get_payment(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


@router.put("/{payment_id}", response_model=PaymentResponse)
async def update_payment(
    payment_id: int,
    data: PaymentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = PaymentService(db)
    try:
        payment = await service.update_payment(payment_id, data)
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        return payment
    except PaymentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except OverpaymentError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payment(
    payment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = PaymentService(db)
    deleted = await service.delete_payment(payment_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Payment not found")
    return None