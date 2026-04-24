from sqlalchemy import JSON, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import AssetModality
from app.models.mixins import TimestampMixin


class Asset(TimestampMixin, Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    shot_id: Mapped[int] = mapped_column(ForeignKey("shots.id"), nullable=False, index=True)
    asset_task_id: Mapped[int] = mapped_column(ForeignKey("asset_tasks.id"), nullable=False, index=True)
    modality: Mapped[AssetModality] = mapped_column(Enum(AssetModality), nullable=False)
    provider_name: Mapped[str] = mapped_column(String(100), nullable=False)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    shot = relationship("Shot", back_populates="assets")
    asset_task = relationship("AssetTask", back_populates="assets")

    @property
    def asset_type(self) -> AssetModality:
        return self.modality

    @property
    def url(self) -> str:
        return self.file_url
