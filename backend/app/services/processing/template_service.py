from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models.processing.processing_template import ProcessingTemplate
from app.repositories.processing.template_repository import TemplateRepository


class TemplateService:
    """
    Business logic for processing templates.
    """

    def __init__(self, db: Session):
        self.db = db
        self.repository = TemplateRepository(db)

    def create_template(
        self,
        *,
        name: str,
        document_type: str,
        schema: dict,
        description: str | None = None,
    ) -> ProcessingTemplate:

        template = ProcessingTemplate(
            name=name,
            document_type=document_type,
            description=description,
            schema=schema,
            is_active=True,
        )

        return self.repository.create(template)

    def get_template(
        self,
        template_id: uuid.UUID,
    ) -> ProcessingTemplate | None:
        return self.repository.get(template_id)

    def list_templates(self):
        return self.repository.list()

    def update_template(
        self,
        template_id: uuid.UUID,
        **updates,
    ) -> ProcessingTemplate | None:

        template = self.repository.get(template_id)

        if not template:
            return None

        for key, value in updates.items():
            if hasattr(template, key):
                setattr(template, key, value)

        return self.repository.update(template)

    def activate(
        self,
        template_id: uuid.UUID,
    ) -> ProcessingTemplate | None:

        template = self.repository.get(template_id)

        if not template:
            return None

        template.is_active = True
        return self.repository.update(template)

    def deactivate(
        self,
        template_id: uuid.UUID,
    ) -> ProcessingTemplate | None:

        template = self.repository.get(template_id)

        if not template:
            return None

        template.is_active = False
        return self.repository.update(template)

    def delete_template(
        self,
        template_id: uuid.UUID,
    ) -> bool:
        return self.repository.delete(template_id)