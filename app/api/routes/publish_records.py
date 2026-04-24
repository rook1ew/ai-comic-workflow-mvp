from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.schemas.publish_record import PublishRecordCreate, PublishRecordResponse
from app.services.publish_service import create_publish_record

router = APIRouter()


@router.post("/publish-records", response_model=PublishRecordResponse, status_code=201)
def create_publish_record_route(payload: PublishRecordCreate, db: Session = Depends(get_db)) -> PublishRecordResponse:
    return create_publish_record(db, payload)
