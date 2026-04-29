from app.common.exceptions.base import ClinicException


class TemplateNotFoundError(ClinicException):
    pass

class NotificationSendError(ClinicException):
    pass