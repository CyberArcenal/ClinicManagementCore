# app/common/schema/response.py
from typing import Generic, TypeVar, Any
from pydantic import BaseModel

T = TypeVar('T')

class SuccessResponse(BaseModel, Generic[T]):
    status: bool = True
    message: str = "Success"
    data: T