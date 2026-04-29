from app.common.exceptions.base import ClinicException


class LabTechNotFoundError(ClinicException):
    pass

class InvalidLabStatusTransitionError(ClinicException):
    pass

class LabResultNotFoundError(ClinicException):
    pass