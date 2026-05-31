"""Add composite indexes for user-scoped queries

Revision ID: add_composite_idx_001
Revises: a1b2c3d4e5f6
Create Date: 2026-05-11

Adds composite indexes to speed up the two most common user-scoped
list queries:
  - saved_papers:   WHERE user_id = ? ORDER BY saved_at DESC
  - search_alerts:  WHERE user_id = ? ORDER BY created_at DESC
"""

from collections.abc import Sequence

from alembic import op

revision: str = "add_composite_idx_001"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("saved_papers") as batch_op:
        batch_op.create_index(
            "ix_saved_papers_user_id_saved_at",
            ["user_id", "saved_at"],
        )

    with op.batch_alter_table("search_alerts") as batch_op:
        batch_op.create_index(
            "ix_search_alerts_user_id_created_at",
            ["user_id", "created_at"],
        )


def downgrade() -> None:
    with op.batch_alter_table("search_alerts") as batch_op:
        batch_op.drop_index("ix_search_alerts_user_id_created_at")

    with op.batch_alter_table("saved_papers") as batch_op:
        batch_op.drop_index("ix_saved_papers_user_id_saved_at")
