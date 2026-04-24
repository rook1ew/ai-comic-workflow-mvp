from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.publish_record import PublishRecord
from app.schemas.publish_record import PublishRecordCreate
from app.services.repository import create_and_refresh


def create_publish_record(db: Session, payload: PublishRecordCreate) -> PublishRecord:
    if db.get(Project, payload.project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    record = PublishRecord(**payload.model_dump())
    return create_and_refresh(db, record)
