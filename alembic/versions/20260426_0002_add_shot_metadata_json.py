"""add metadata_json to shots"""

from alembic import op
import sqlalchemy as sa


revision = "20260426_0002"
down_revision = "20260425_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("shots", sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")))


def downgrade() -> None:
    op.drop_column("shots", "metadata_json")
