# app/modules/inventory/api/v1/__init__.py
from fastapi import APIRouter
from .endpoints.inventory_item import router as item_router
from .endpoints.inventory_transaction import router as transaction_router

router = APIRouter()
router.include_router(item_router, prefix="/inventory-items", tags=["Inventory Items"])
router.include_router(transaction_router, prefix="/inventory-transactions", tags=["Inventory Transactions"])