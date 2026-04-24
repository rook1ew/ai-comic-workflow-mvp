from datetime import datetime

from sqlalchemy import DateTime, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import ReviewConclusion, ReviewTargetType
from app.models.mixins import TimestampMixin


class Review(TimestampMixin, Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    target_type: Mapped[ReviewTargetType] = mapped_column(Enum(ReviewTargetType), nullable=False)
    target_id: Mapped[int] = mapped_column(Integer, nullable=False)
    conclusion: Mapped[ReviewConclusion] = mapped_column(Enum(ReviewConclusion), nullable=False)
    issue_description: Mapped[str] = mapped_column(Text, nullable=False)
    revision_suggestion: Mapped[str] = mapped_column(Text, nullable=False)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    reviewer: Mapped[str] = mapped_column(String(255), nullable=False)
