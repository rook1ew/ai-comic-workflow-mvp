"""add metadata_json to episodes"""

from alembic import op
import sqlalchemy as sa


revision = "20260429_0004"
down_revision = "20260427_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "episodes",
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
    )


def downgrade() -> None:
    op.drop_column("episodes", "metadata_json")
