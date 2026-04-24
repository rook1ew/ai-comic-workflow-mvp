from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.schemas.shot import ShotCreate, ShotResponse
from app.services.shot_service import create_shot

router = APIRouter()


@router.post("/shots", response_model=ShotResponse, status_code=201)
def create_shot_route(payload: ShotCreate, db: Session = Depends(get_db)) -> ShotResponse:
    return create_shot(db, payload)
