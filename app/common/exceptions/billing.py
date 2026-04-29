
from app.common.exceptions.base import ClinicException


class InvoiceNotFoundError(ClinicException):
    pass

class InvoiceAlreadyPaidError(ClinicException):
    pass

class OverpaymentError(ClinicException):
    pass

class InvalidPaymentAmountError(ClinicException):
    pass

class BillingItemNotFoundError(ClinicException):
    pass

class PaymentNotFoundError(ClinicException):
    pass