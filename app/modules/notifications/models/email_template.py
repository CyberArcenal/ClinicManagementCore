# app/models/notifications/email_template.py
from sqlalchemy import Column, String, Text
from sqlalchemy.sql import func

from app.common.models.base import BaseModel
from app.modules.notifications.enums.base import TemplateType


class EmailTemplate(BaseModel):
    __tablename__ = "email_templates"

    name = Column(String(100), nullable=False, unique=True)
    subject = Column(String(200), nullable=False)
    content = Column(Text, nullable=False, comment="Use {{ subscriber.email }} for dynamic content")
    # BaseModel already provides created_at, updated_at
    # but Django has modified_at -> we reuse updated_at

    def __repr__(self):
        return f"<EmailTemplate {self.name}>"