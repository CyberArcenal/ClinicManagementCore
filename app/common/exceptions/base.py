# app/common/exceptions.py
class ClinicException(Exception):
    """Base exception for clinic app."""
    pass

class DoctorNotFoundError(ClinicException):
    pass

class PatientNotFoundError(ClinicException):
    pass

class AppointmentConflictError(ClinicException):
    pass

class DoctorUnavailableError(ClinicException):
    pass

class InvalidStatusTransitionError(ClinicException):
    pass


