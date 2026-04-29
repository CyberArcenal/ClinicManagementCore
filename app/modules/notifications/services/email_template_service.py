# app/modules/notifications/email_template_service.py
from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select

from app.common.exceptions.notification import TemplateNotFoundError
from app.common.schema.base import PaginatedResponse
from app.modules.notifications.models.email_template import EmailTemplate
from app.modules.notifications.schemas.base import EmailTemplateCreate, EmailTemplateUpdate



class EmailTemplateService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    async def get_template(self, template_id: int) -> Optional[EmailTemplate]:
        result = await self.db.execute(
            select(EmailTemplate).where(EmailTemplate.id == template_id)
        )
        return result.scalar_one_or_none()

    async def get_template_by_name(self, name: str) -> Optional[EmailTemplate]:
        result = await self.db.execute(
            select(EmailTemplate).where(EmailTemplate.name == name)
        )
        return result.scalar_one_or_none()

    async def get_templates(
        self,
        page: int = 1,
        page_size: int = 100,
    ) -> PaginatedResponse[EmailTemplate]:
        query = select(EmailTemplate)
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        result = await self.db.execute(query)
        items = result.scalars().all()
        pages = (total + page_size - 1) // page_size if total > 0 else 0
        return PaginatedResponse(items=items, total=total, page=page, size=page_size, pages=pages)

    async def create_template(self, data: EmailTemplateCreate) -> EmailTemplate:
        template = EmailTemplate(
            name=data.name,
            subject=data.subject,
            content=data.content,
        )
        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)
        return template

    async def update_template(
        self, template_id: int, data: EmailTemplateUpdate
    ) -> EmailTemplate:
        template = await self.get_template(template_id)
        if not template:
            raise TemplateNotFoundError(f"Template {template_id} not found")
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(template, key, value)
        await self.db.commit()
        await self.db.refresh(template)
        return template

    async def delete_template(self, template_id: int) -> bool:
        template = await self.get_template(template_id)
        if not template:
            return False
        await self.db.delete(template)
        await self.db.commit()
        return True

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    @staticmethod
    def render_template(template: EmailTemplate, context: Dict[str, str]) -> tuple[str, str]:
        """
        Replace placeholders like {{ variable }} in subject and content.
        Returns (rendered_subject, rendered_content).
        """
        subject = template.subject
        content = template.content
        for key, value in context.items():
            subject = subject.replace(f"{{{{ {key} }}}}", str(value))
            subject = subject.replace(f"{{{{ {key} }}}}", str(value))
            content = content.replace(f"{{{{ {key} }}}}", str(value))
            content = content.replace(f"{{{{ {key} }}}}", str(value))
        return subject, content

    async def render_by_name(self, name: str, context: Dict[str, str]) -> tuple[str, str]:
        template = await self.get_template_by_name(name)
        if not template:
            raise TemplateNotFoundError(f"Template '{name}' not found")
        return self.render_template(template, context)
    
    def get_template_by_name_sync(self, name: str):
        return self.db.query(EmailTemplate).filter(EmailTemplate.name == name).first()

    def render_template_sync(self, template: EmailTemplate, context: dict) -> tuple:
        # Simple Jinja2-like replacement, or use Jinja2 if installed
        subject = template.subject
        content = template.content
        for key, value in context.items():
            subject = subject.replace(f"{{{{ {key} }}}}", str(value))
            content = content.replace(f"{{{{ {key} }}}}", str(value))
        return subject, content