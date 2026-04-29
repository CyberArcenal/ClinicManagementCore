from app.common.exceptions.base import ClinicException


class UserNotFoundError(ClinicException):
    pass

class InvalidCredentialsError(ClinicException):
    pass

class UserAlreadyExistsError(ClinicException):
    pass