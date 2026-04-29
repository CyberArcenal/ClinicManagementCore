from app.common.exceptions.base import ClinicException


class PrescriptionNotFoundError(ClinicException):
    pass

class PrescriptionItemNotFoundError(ClinicException):
    pass