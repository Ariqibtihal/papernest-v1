"""add account lockout fields

Revision ID: add_lockout_001
Revises: fc7b40e75078
Create Date: 2026-05-08 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_lockout_001'
down_revision: Union[str, None] = 'fc7b40e75078'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add account lockout fields to users table
    op.add_column('users', sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('locked_until', sa.DateTime(), nullable=True))


def downgrade() -> None:
    # Remove account lockout fields
    op.drop_column('users', 'locked_until')
    op.drop_column('users', 'failed_login_attempts')
