"""Add user_id to saved_papers and search_alerts for data isolation

Revision ID: a1b2c3d4e5f6
Revises: add_account_lockout_fields
Create Date: 2026-05-09

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "add_lockout_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add user_id to saved_papers (nullable for backward compat with existing rows)
    with op.batch_alter_table("saved_papers") as batch_op:
        batch_op.add_column(sa.Column("user_id", sa.Integer(), nullable=True))
        batch_op.create_index("ix_saved_papers_user_id", ["user_id"])
        batch_op.create_foreign_key(
            "fk_saved_papers_user_id", "users", ["user_id"], ["id"], ondelete="CASCADE"
        )

    # Add user_id to search_alerts (nullable for backward compat)
    with op.batch_alter_table("search_alerts") as batch_op:
        batch_op.add_column(sa.Column("user_id", sa.Integer(), nullable=True))
        batch_op.create_index("ix_search_alerts_user_id", ["user_id"])
        batch_op.create_foreign_key(
            "fk_search_alerts_user_id", "users", ["user_id"], ["id"], ondelete="CASCADE"
        )


def downgrade() -> None:
    with op.batch_alter_table("search_alerts") as batch_op:
        batch_op.drop_constraint("fk_search_alerts_user_id", type_="foreignkey")
        batch_op.drop_index("ix_search_alerts_user_id")
        batch_op.drop_column("user_id")

    with op.batch_alter_table("saved_papers") as batch_op:
        batch_op.drop_constraint("fk_saved_papers_user_id", type_="foreignkey")
        batch_op.drop_index("ix_saved_papers_user_id")
        batch_op.drop_column("user_id")
