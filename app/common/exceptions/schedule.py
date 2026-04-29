from app.common.exceptions.base import ClinicException


class ScheduleNotFoundError(ClinicException):
    pass

class ScheduleConflictError(ClinicException):
    pass