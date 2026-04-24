from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.models.enums import ReviewTargetType
from app.models.project import Project
from app.models.review import Review
from app.models.shot import Shot
from app.schemas.review import ReviewCreate
from app.services.repository import create_and_refresh


def create_review(db: Session, payload: ReviewCreate) -> Review:
    model_map = {
        ReviewTargetType.PROJECT: Project,
        ReviewTargetType.SHOT: Shot,
        ReviewTargetType.ASSET: Asset,
    }
    model = model_map[payload.target_type]
    if db.get(model, payload.target_id) is None:
        raise HTTPException(status_code=404, detail=f"{payload.target_type.value} target not found")
    review = Review(**payload.model_dump())
    return create_and_refresh(db, review)
