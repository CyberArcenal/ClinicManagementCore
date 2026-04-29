from app.common.exceptions.base import ClinicException


class RoomNotFoundError(ClinicException):
    pass

class RoomNotAvailableError(ClinicException):
    pass