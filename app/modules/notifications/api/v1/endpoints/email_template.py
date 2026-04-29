# app/modules/notification/api/v1/endpoints/email_template.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.api.db import get_db
from app.common.dependencies.auth import require_role
from app.common.schema.base import PaginatedResponse
from app.modules.notifications.schemas.base import EmailTemplateCreate, EmailTemplateResponse
from app.modules.notifications.services.email_template_service import EmailTemplateService
from app.modules.user.models import User

router = APIRouter()


@router.post("/", response_model=EmailTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_email_template(
    data: EmailTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = EmailTemplateService(db)
    template = await service.create_template(data)
    return template


@router.get("/", response_model=PaginatedResponse[EmailTemplateResponse])
async def list_email_templates(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=1000, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = EmailTemplateService(db)
    paginated = await service.get_templates(page=page, page_size=page_size)
    return paginated


@router.get("/{template_id}", response_model=EmailTemplateResponse)
async def get_email_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = EmailTemplateService(db)
    template = await service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Email template not found")
    return template


@router.put("/{template_id}", response_model=EmailTemplateResponse)
async def update_email_template(
    template_id: int,
    data: EmailTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = EmailTemplateService(db)
    try:
        template = await service.update_template(template_id, data)
        return template
    except TemplateNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_email_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = EmailTemplateService(db)
    deleted = await service.delete_template(template_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Email template not found")
    return None


@router.post("/render/{template_name}")
async def render_template(
    template_name: str,
    context: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = EmailTemplateService(db)
    try:
        subject, content = await service.render_by_name(template_name, context)
        return {"subject": subject, "content": content}
    except TemplateNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))