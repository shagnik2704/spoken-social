"""add minitask_opted to user_tutorials

Revision ID: b7f2a1c3d4e5
Revises: afd1d573b483
Create Date: 2026-03-29 21:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7f2a1c3d4e5'
down_revision: Union[str, Sequence[str], None] = 'afd1d573b483'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add minitask_opted column to user_tutorials."""
    op.add_column('user_tutorials', sa.Column('minitask_opted', sa.Boolean(), server_default='false', nullable=True))


def downgrade() -> None:
    """Remove minitask_opted column from user_tutorials."""
    op.drop_column('user_tutorials', 'minitask_opted')
