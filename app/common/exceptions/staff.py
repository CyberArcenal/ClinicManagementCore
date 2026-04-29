from app.common.exceptions.base import ClinicException


class DoctorNotFoundError(ClinicException):
    pass

class NurseNotFoundError(ClinicException):
    pass

class ReceptionistNotFoundError(ClinicException):
    pass

class LabTechNotFoundError(ClinicException):
    pass

class PharmacistNotFoundError(ClinicException):
    pass

class DuplicateLicenseError(ClinicException):
    pass