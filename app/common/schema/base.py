# app/schemas/base.py
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # ORM mode

class TimestampSchema(BaseSchema):
    id: int
    created_at: datetime
    updated_at: datetime