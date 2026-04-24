from sqlalchemy import JSON, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import AssetModality, AssetTaskStatus
from app.models.mixins import TimestampMixin


class AssetTask(TimestampMixin, Base):
    __tablename__ = "asset_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    shot_id: Mapped[int] = mapped_column(ForeignKey("shots.id"), nullable=False, index=True)
    modality: Mapped[AssetModality] = mapped_column(Enum(AssetModality), nullable=False)
    status: Mapped[AssetTaskStatus] = mapped_column(Enum(AssetTaskStatus), default=AssetTaskStatus.QUEUED, nullable=False)
    retry_count: Mapped[int] = mapped_column(default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(default=3, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider_name: Mapped[str] = mapped_column(String(100), nullable=False, default="mock")
    input_payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    output_payload: Mapped[dict | None] = mapped_column(JSON, default=None, nullable=True)

    shot = relationship("Shot", back_populates="asset_tasks")
    assets = relationship("Asset", back_populates="asset_task", cascade="all, delete-orphan")
