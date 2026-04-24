from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import TimestampedResponse


class PublishRecordCreate(BaseModel):
    project_id: int
    platform: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=255)
    published_at: datetime
    link: str = Field(min_length=1, max_length=500)


class PublishRecordResponse(TimestampedResponse):
    project_id: int
    platform: str
    title: str
    published_at: datetime
    link: str
