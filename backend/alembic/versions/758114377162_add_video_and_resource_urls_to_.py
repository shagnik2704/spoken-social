"""add_video_and_resource_urls_to_tutorials_and_contents

Revision ID: 758114377162
Revises: d2e3f4a5b6c7
Create Date: 2026-11-04 19:13:21.966867

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '758114377162'
down_revision: Union[str, Sequence[str], None] = 'd2e3f4a5b6c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add video and companion resource columns to tutorials table
    op.add_column('tutorials', sa.Column('video_url', sa.Text(), nullable=True))
    op.add_column('tutorials', sa.Column('video_poster_url', sa.Text(), nullable=True))
    op.add_column('tutorials', sa.Column('code_files_url', sa.Text(), nullable=True))
    op.add_column('tutorials', sa.Column('instruction_sheet_url', sa.Text(), nullable=True))
    op.add_column('tutorials', sa.Column('assignment_url', sa.Text(), nullable=True))
    op.add_column('tutorials', sa.Column('assignment_instructions', sa.Text(), nullable=True))

    # 2. Add video and companion resource columns to tutorial_contents table
    op.add_column('tutorial_contents', sa.Column('video_url', sa.Text(), nullable=True))
    op.add_column('tutorial_contents', sa.Column('video_poster_url', sa.Text(), nullable=True))
    op.add_column('tutorial_contents', sa.Column('video_duration_seconds', sa.Integer(), nullable=True))
    op.add_column('tutorial_contents', sa.Column('code_files_url', sa.Text(), nullable=True))
    op.add_column('tutorial_contents', sa.Column('instruction_sheet_url', sa.Text(), nullable=True))
    op.add_column('tutorial_contents', sa.Column('assignment_url', sa.Text(), nullable=True))
    op.add_column('tutorial_contents', sa.Column('assignment_instructions', sa.Text(), nullable=True))


def downgrade() -> None:
    # Downgrade tutorial_contents
    op.drop_column('tutorial_contents', 'assignment_instructions')
    op.drop_column('tutorial_contents', 'assignment_url')
    op.drop_column('tutorial_contents', 'instruction_sheet_url')
    op.drop_column('tutorial_contents', 'code_files_url')
    op.drop_column('tutorial_contents', 'video_duration_seconds')
    op.drop_column('tutorial_contents', 'video_poster_url')
    op.drop_column('tutorial_contents', 'video_url')

    # Downgrade tutorials
    op.drop_column('tutorials', 'assignment_instructions')
    op.drop_column('tutorials', 'assignment_url')
    op.drop_column('tutorials', 'instruction_sheet_url')
    op.drop_column('tutorials', 'code_files_url')
    op.drop_column('tutorials', 'video_poster_url')
    op.drop_column('tutorials', 'video_url')
