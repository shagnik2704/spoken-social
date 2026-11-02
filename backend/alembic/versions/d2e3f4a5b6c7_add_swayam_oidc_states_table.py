"""add swayam_oidc_states table

Revision ID: d2e3f4a5b6c7
Revises: c1d2e3f4a5b6
Create Date: 2026-11-02
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'd2e3f4a5b6c7'
down_revision: Union[str, Sequence[str], None] = 'c1d2e3f4a5b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'swayam_oidc_states',
        sa.Column('state', sa.String(length=128), primary_key=True),
        sa.Column('nonce', sa.String(length=128), nullable=False),
        sa.Column('code_verifier', sa.String(length=128), nullable=False),
        sa.Column('login_hint', sa.String(length=255), nullable=True),
        sa.Column('enrollment_id', sa.String(length=255), nullable=True),
        sa.Column('target_link_uri', sa.String(length=1024), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('idx_swayam_oidc_states_created_at', 'swayam_oidc_states', ['created_at'])


def downgrade() -> None:
    op.drop_index('idx_swayam_oidc_states_created_at', table_name='swayam_oidc_states')
    op.drop_table('swayam_oidc_states')
