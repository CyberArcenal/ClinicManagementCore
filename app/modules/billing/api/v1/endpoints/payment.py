from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.common.api.db import get_db
from app.common.dependencies.auth import get_current_user, require_role
from app.common.exceptions.billing import InvoiceNotFoundError, OverpaymentError, PaymentNotFoundError
from app.common.schema.base import PaginatedResponse
from app.common.schema.response import SuccessResponse
from app.common.utils.response import success_response
from app.modules.billing.enums.base import PaymentMethod
from app.modules.billing.schemas.base import PaymentCreate, PaymentResponse, PaymentUpdate
from app.modules.billing.services.payment import PaymentService
from app.modules.user.models.user import User

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_payment(
    data: PaymentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("receptionist")),
) -> SuccessResponse[PaymentResponse]:
    service = PaymentService(db)
    try:
        payment = await service.create_payment(data)
        return success_response(data=payment, message="Payment created")
    except InvoiceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except OverpaymentError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/")
async def list_payments(
    invoice_id: Optional[int] = Query(None),
    method: Optional[PaymentMethod] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[PaginatedResponse[PaymentResponse]]:
    filters = {}
    if invoice_id:
        filters["invoice_id"] = invoice_id
    if method:
        filters["method"] = method
    if date_from:
        filters["date_from"] = date_from
    if date_to:
        filters["date_to"] = date_to

    service = PaymentService(db)
    paginated = await service.get_payments(
        filters=filters,
        page=page,
        page_size=page_size,
    )
    return success_response(data=paginated, message="Payments retrieved")


@router.get("/{payment_id}")
async def get_payment(
    payment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[PaymentResponse]:
    service = PaymentService(db)
    payment = await service.get_payment(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return success_response(data=payment, message="Payment retrieved")


@router.put("/{payment_id}")
async def update_payment(
    payment_id: int,
    data: PaymentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> SuccessResponse[PaymentResponse]:
    service = PaymentService(db)
    try:
        payment = await service.update_payment(payment_id, data)
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        return success_response(data=payment, message="Payment updated")
    except PaymentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except OverpaymentError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payment(
    payment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> None:
    service = PaymentService(db)
    deleted = await service.delete_payment(payment_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Payment not found")
    return None