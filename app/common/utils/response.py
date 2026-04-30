from typing import Any
from app.common.schema.response import SuccessResponse

def success_response(data: Any = None, message: str = "Success") -> SuccessResponse:
    return SuccessResponse(message=message, data=data)