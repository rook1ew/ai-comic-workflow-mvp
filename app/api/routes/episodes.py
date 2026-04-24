from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.schemas.episode import EpisodeCreate, EpisodeResponse
from app.services.episode_service import create_episode

router = APIRouter()


@router.post("/episodes", response_model=EpisodeResponse, status_code=201)
def create_episode_route(payload: EpisodeCreate, db: Session = Depends(get_db)) -> EpisodeResponse:
    return create_episode(db, payload)
