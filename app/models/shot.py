from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ShotStatus
from app.models.mixins import TimestampMixin


class Shot(TimestampMixin, Base):
    __tablename__ = "shots"

    id: Mapped[int] = mapped_column(primary_key=True)
    scene_id: Mapped[int] = mapped_column(ForeignKey("scenes.id"), nullable=False, index=True)
    shot_number: Mapped[int] = mapped_column(nullable=False)
    framing: Mapped[str] = mapped_column(String(100), nullable=False)
    core_action: Mapped[str] = mapped_column(Text, nullable=False)
    dialogue: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    video_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    voice_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    bgm_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ShotStatus] = mapped_column(Enum(ShotStatus), default=ShotStatus.PENDING, nullable=False)

    scene = relationship("Scene", back_populates="shots")
    asset_tasks = relationship("AssetTask", back_populates="shot", cascade="all, delete-orphan")
    assets = relationship("Asset", back_populates="shot", cascade="all, delete-orphan")
