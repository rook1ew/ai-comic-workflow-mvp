from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin


class Character(TimestampMixin, Base):
    __tablename__ = "characters"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role_type: Mapped[str] = mapped_column(String(100), nullable=False)
    profile: Mapped[str] = mapped_column(Text, nullable=False)
    visual_notes: Mapped[str] = mapped_column(Text, nullable=False)
    voice_style: Mapped[str] = mapped_column(Text, nullable=False)
    main_reference_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    main_reference_confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    project = relationship("Project", back_populates="characters")
