from sqlalchemy import Boolean, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin


class CharacterAppearance(TimestampMixin, Base):
    __tablename__ = "character_appearances"
    __table_args__ = (
        UniqueConstraint("character_id", "appearance_key", name="uq_character_appearance_key"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id"), nullable=False, index=True)
    appearance_key: Mapped[str] = mapped_column(String(255), nullable=False)
    appearance_type: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    is_selected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    change_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    must_keep_json: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    avoid_json: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    character = relationship("Character", back_populates="appearances")
