"""add_programmes_table_and_fks

Revision ID: f1a2b3c4d5e6
Revises: cf9a1ff8d355
Create Date: 2026-06-11 17:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, None] = 'cf9a1ff8d355'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create programmes table
    op.create_table(
        'programmes',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('icon', sa.String(50)),
        sa.Column('color', sa.String(100)),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('display_order', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # 2. Seed the 3 programme records
    op.execute("""
        INSERT INTO programmes (id, name, description, icon, color, is_active, display_order) VALUES
        ('fdp', 'FDP', 'Faculty Development Programme — National Summer FDP courses on Linux, Python, LaTeX, and Scilab', 'graduation-cap', 'from-violet-500 to-purple-600', true, 1),
        ('swayam_plus', 'Swayam Plus', 'Swayam Plus — semester-long courses on Linux, PostgreSQL, AI, and Python for Handling Data', 'book-open', 'from-blue-500 to-cyan-500', true, 2),
        ('ilw', 'ILW', 'Internship & Learning Workshop — hands-on workshops on Web Development, Data Analytics, and IoT', 'laptop', 'from-emerald-500 to-teal-500', true, 3)
        ON CONFLICT (id) DO NOTHING;
    """)

    # 3. Create programme_courses M2M junction table
    op.create_table(
        'programme_courses',
        sa.Column('programme_id', sa.String(50), sa.ForeignKey('programmes.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('course_id', sa.String(50), sa.ForeignKey('courses.id', ondelete='CASCADE'), primary_key=True),
    )

    # 4. Add programme_id to batches
    op.add_column('batches', sa.Column('programme_id', sa.String(50), sa.ForeignKey('programmes.id', ondelete='SET NULL'), nullable=True))

    # 5. Tag existing FDP batches (all current batches are FDP)
    op.execute("UPDATE batches SET programme_id = 'fdp' WHERE programme_id IS NULL")

    # 6. Link existing courses to FDP programme
    op.execute("""
        INSERT INTO programme_courses (programme_id, course_id)
        SELECT 'fdp', id FROM courses
        ON CONFLICT DO NOTHING;
    """)

    # 7. Alter college_courses: drop old PK, add programme_id column, create new PK
    # First add the column with a default
    op.add_column('college_courses', sa.Column('programme_id', sa.String(50), server_default='fdp', nullable=False))

    # Add FK constraint
    op.create_foreign_key(
        'fk_college_courses_programme',
        'college_courses',
        'programmes',
        ['programme_id'],
        ['id'],
        ondelete='CASCADE'
    )

    # Drop old PK and create new composite PK including programme_id
    op.drop_constraint('college_courses_pkey', 'college_courses', type_='primary')
    op.create_primary_key('college_courses_pkey', 'college_courses', ['college_id', 'course_id', 'programme_id'])


def downgrade() -> None:
    # Reverse college_courses PK change
    op.drop_constraint('college_courses_pkey', 'college_courses', type_='primary')
    op.create_primary_key('college_courses_pkey', 'college_courses', ['college_id', 'course_id'])
    op.drop_constraint('fk_college_courses_programme', 'college_courses', type_='foreignkey')
    op.drop_column('college_courses', 'programme_id')

    # Remove programme_id from batches
    op.drop_column('batches', 'programme_id')

    # Drop programme_courses junction
    op.drop_table('programme_courses')

    # Drop programmes table
    op.drop_table('programmes')
