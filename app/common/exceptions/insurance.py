from app.common.exceptions.base import ClinicException


class InsuranceDetailNotFoundError(ClinicException):
    pass


class InsuranceCoverageExpiredError(ClinicException):
    pass


class DuplicateInsuranceError(ClinicException):
    pass


class ClaimAmountExceedsInvoiceError(ClinicException):
    pass


class InsuranceClaimNotFoundError(ClinicException):
    pass
