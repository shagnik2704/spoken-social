"""add swayam_sub to users and swayam_enrollment_id to user_courses

Revision ID: c1d2e3f4a5b6
Revises: b9c0d1e2f3a4
Create Date: 2026-11-02
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'c1d2e3f4a5b6'
down_revision: Union[str, Sequence[str], None] = 'b9c0d1e2f3a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add swayam_sub to users table
    op.add_column(
        'users',
        sa.Column('swayam_sub', sa.String(length=255), nullable=True)
    )
    op.create_index('idx_users_swayam_sub', 'users', ['swayam_sub'], unique=True)

    # 2. Add swayam_enrollment_id to user_courses table
    op.add_column(
        'user_courses',
        sa.Column('swayam_enrollment_id', sa.String(length=255), nullable=True)
    )
    op.create_index('idx_user_courses_swayam_enrollment_id', 'user_courses', ['swayam_enrollment_id'])


def downgrade() -> None:
    op.drop_index('idx_user_courses_swayam_enrollment_id', table_name='user_courses')
    op.drop_column('user_courses', 'swayam_enrollment_id')
    op.drop_index('idx_users_swayam_sub', table_name='users')
    op.drop_column('users', 'swayam_sub')
