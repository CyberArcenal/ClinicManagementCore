from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Generic, TypeVar, List
from pydantic import BaseModel, Field

T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number (1-indexed)")
    size: int = Field(..., description="Items per page")
    pages: int = Field(..., description="Total number of pages")