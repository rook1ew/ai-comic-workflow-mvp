from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.episode import Episode
from app.models.project import Project
from app.schemas.episode import EpisodeCreate
from app.services.repository import create_and_refresh


def create_episode(db: Session, payload: EpisodeCreate) -> Episode:
    if db.get(Project, payload.project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    episode = Episode(**payload.model_dump())
    return create_and_refresh(db, episode)


def get_or_create_default_episode(db: Session, project_id: int) -> Episode:
    if db.get(Project, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    episode = (
        db.query(Episode)
        .filter(Episode.project_id == project_id)
        .order_by(Episode.episode_number.asc(), Episode.id.asc())
        .first()
    )
    if episode is not None:
        return episode
    return create_episode(
        db,
        EpisodeCreate(
            project_id=project_id,
            title="Episode 1",
            episode_number=1,
            script_card=None,
        ),
    )


def update_episode_script_card(db: Session, episode_id: int, script_card: str) -> Episode:
    episode = db.get(Episode, episode_id)
    if episode is None:
        raise HTTPException(status_code=404, detail="Episode not found")
    episode.script_card = script_card
    db.commit()
    db.refresh(episode)
    return episode
