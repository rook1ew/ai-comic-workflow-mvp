from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import ReviewConclusion, ReviewTargetType
from app.schemas.common import TimestampedResponse


class ReviewCreate(BaseModel):
    target_type: ReviewTargetType
    target_id: int = Field(ge=1)
    conclusion: ReviewConclusion
    issue_description: str = Field(min_length=1)
    revision_suggestion: str = Field(min_length=1)
    reviewed_at: datetime
    reviewer: str = Field(min_length=1, max_length=255)


class ReviewResponse(TimestampedResponse):
    target_type: ReviewTargetType
    target_id: int
    conclusion: ReviewConclusion
    issue_description: str
    revision_suggestion: str
    reviewed_at: datetime
    reviewer: str
