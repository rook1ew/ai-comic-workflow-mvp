"""add character appearances

Revision ID: 20260429_0005
Revises: 20260429_0004
Create Date: 2026-04-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260429_0005"
down_revision: str | None = "20260429_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "character_appearances",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("character_id", sa.Integer(), nullable=False),
        sa.Column("appearance_key", sa.String(length=255), nullable=False),
        sa.Column("appearance_type", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("image_url", sa.String(length=1000), nullable=False),
        sa.Column("is_selected", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("order_index", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("change_reason", sa.Text(), nullable=True),
        sa.Column("must_keep_json", sa.JSON(), server_default=sa.text("'[]'"), nullable=False),
        sa.Column("avoid_json", sa.JSON(), server_default=sa.text("'[]'"), nullable=False),
        sa.Column("metadata_json", sa.JSON(), server_default=sa.text("'{}'"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["character_id"], ["characters.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("character_id", "appearance_key", name="uq_character_appearance_key"),
    )
    op.create_index(op.f("ix_character_appearances_character_id"), "character_appearances", ["character_id"], unique=False)
    op.create_index(op.f("ix_character_appearances_project_id"), "character_appearances", ["project_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_character_appearances_project_id"), table_name="character_appearances")
    op.drop_index(op.f("ix_character_appearances_character_id"), table_name="character_appearances")
    op.drop_table("character_appearances")
