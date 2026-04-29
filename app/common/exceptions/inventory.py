from app.common.exceptions.base import ClinicException


class InventoryItemNotFoundError(ClinicException):
    pass


class InsufficientStockError(ClinicException):
    pass


class InvalidTransactionTypeError(ClinicException):
    pass


class InventoryTransactionNotFoundError(ClinicException):
    pass
