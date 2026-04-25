from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.scene import Scene
from app.models.shot import Shot
from app.schemas.shot import ShotCreate
from app.services.repository import create_and_refresh


def create_shot(db: Session, payload: ShotCreate) -> Shot:
    if db.get(Scene, payload.scene_id) is None:
        raise HTTPException(status_code=404, detail="Scene not found")
    shot = Shot(**payload.model_dump())
    return create_and_refresh(db, shot)


def update_shot_metadata(db: Session, shot_id: int, metadata_json: dict) -> Shot:
    shot = db.get(Shot, shot_id)
    if shot is None:
        raise HTTPException(status_code=404, detail="Shot not found")
    shot.metadata_json = metadata_json
    db.commit()
    db.refresh(shot)
    return shot
