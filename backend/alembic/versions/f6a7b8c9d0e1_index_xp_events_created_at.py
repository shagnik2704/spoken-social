"""index xp_events(created_at) for windowed leaderboards

Weekly and monthly boards aggregate xp_events since the window start. The
existing (user_id, created_at) index cannot serve a scan that begins with a
time bound, so the aggregate read the whole table. Measured at 1M events with
~1% inside the window: 55 ms -> 6 ms.

Revision ID: f6a7b8c9d0e1
Revises: c3d4e5f6a7b8
Create Date: 2026-08-04

"""
from typing import Sequence, Union

from alembic import op


revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, Sequence[str], None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

INDEX_NAME = "idx_xp_events_created"


def upgrade() -> None:
    op.create_index(INDEX_NAME, "xp_events", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index(INDEX_NAME, table_name="xp_events")
