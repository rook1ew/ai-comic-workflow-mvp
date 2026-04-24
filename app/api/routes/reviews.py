from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.schemas.review import ReviewCreate, ReviewResponse
from app.services.review_service import create_review

router = APIRouter()


@router.post("/reviews", response_model=ReviewResponse, status_code=201)
def create_review_route(payload: ReviewCreate, db: Session = Depends(get_db)) -> ReviewResponse:
    return create_review(db, payload)
