"""rename personality_dev to empathy-growth-mindset

Renames "Personality and Human Development" (personality_dev) to
"Developing Empathy and Growth Mindset" (empathy-growth-mindset) and moves
the 17 tutorials, quizzes, batches, enrollments, habit logs, and XP events
over cleanly so the full curriculum is live at /courses/empathy-growth-mindset.

Revision ID: a1b2c3d4e5f7
Revises: f8c9d0e1a2b3
Create Date: 2026-11-25 20:20:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = 'a1b2c3d4e5f7'
down_revision: Union[str, Sequence[str], None] = 'f8c9d0e1a2b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        DO $$
        BEGIN
            -- 1. Ensure target course exists with live learner_pack layout & updated title
            INSERT INTO courses (id, title, description, forum_category, ui_layout, created_at)
            VALUES (
                'empathy-growth-mindset',
                'Developing Empathy and Growth Mindset',
                'A 2-credit, 12-week life-skills course covering emotional intelligence, self-awareness, active empathy, and building a growth mindset.',
                'Developing Empathy and Growth Mindset',
                'learner_pack',
                NOW()
            )
            ON CONFLICT (id) DO UPDATE SET
                title = 'Developing Empathy and Growth Mindset',
                forum_category = 'Developing Empathy and Growth Mindset',
                ui_layout = 'learner_pack';

            -- 2. If legacy personality_dev exists, migrate all dependent records cleanly
            IF EXISTS (SELECT 1 FROM courses WHERE id = 'personality_dev') THEN
                -- Preserve richer description if target used a placeholder
                UPDATE courses
                   SET description = COALESCE(
                       (SELECT description FROM courses WHERE id = 'personality_dev'),
                       description
                   )
                 WHERE id = 'empathy-growth-mindset'
                   AND (description IS NULL OR description = '');

                -- Move tutorials (skip if tutorial_number already exists on target)
                UPDATE tutorials t
                   SET course_id = 'empathy-growth-mindset'
                 WHERE t.course_id = 'personality_dev'
                   AND NOT EXISTS (
                       SELECT 1 FROM tutorials t2
                        WHERE t2.course_id = 'empathy-growth-mindset'
                          AND t2.tutorial_number = t.tutorial_number
                   );
                DELETE FROM tutorials WHERE course_id = 'personality_dev';

                -- Move batches
                UPDATE batches
                   SET course_id = 'empathy-growth-mindset'
                 WHERE course_id = 'personality_dev';

                -- Merge programme_courses
                DELETE FROM programme_courses pc
                 WHERE pc.course_id = 'personality_dev'
                   AND EXISTS (
                       SELECT 1 FROM programme_courses pc2
                        WHERE pc2.programme_id = pc.programme_id
                          AND pc2.course_id = 'empathy-growth-mindset'
                   );
                UPDATE programme_courses
                   SET course_id = 'empathy-growth-mindset'
                 WHERE course_id = 'personality_dev';

                -- Merge college_courses
                DELETE FROM college_courses cc
                 WHERE cc.course_id = 'personality_dev'
                   AND EXISTS (
                       SELECT 1 FROM college_courses cc2
                        WHERE cc2.college_id = cc.college_id
                          AND cc2.programme_id = cc.programme_id
                          AND cc2.course_id = 'empathy-growth-mindset'
                   );
                UPDATE college_courses
                   SET course_id = 'empathy-growth-mindset'
                 WHERE course_id = 'personality_dev';

                -- Merge user_courses: preserve higher progress & swayam_enrollment_id on conflict
                UPDATE user_courses dst
                   SET progress_percent = GREATEST(COALESCE(dst.progress_percent, 0), COALESCE(src.progress_percent, 0)),
                       status = CASE
                           WHEN dst.status = 'completed' OR src.status = 'completed' THEN 'completed'
                           WHEN dst.status = 'in_progress' OR src.status = 'in_progress' THEN 'in_progress'
                           ELSE dst.status
                       END,
                       completed_at = COALESCE(dst.completed_at, src.completed_at),
                       swayam_enrollment_id = COALESCE(dst.swayam_enrollment_id, src.swayam_enrollment_id)
                  FROM user_courses src
                 WHERE dst.user_id = src.user_id
                   AND dst.course_id = 'empathy-growth-mindset'
                   AND src.course_id = 'personality_dev';

                DELETE FROM user_courses uc
                 WHERE uc.course_id = 'personality_dev'
                   AND EXISTS (
                       SELECT 1 FROM user_courses uc2
                        WHERE uc2.user_id = uc.user_id
                          AND uc2.course_id = 'empathy-growth-mindset'
                   );
                UPDATE user_courses
                   SET course_id = 'empathy-growth-mindset'
                 WHERE course_id = 'personality_dev';

                -- Merge habit log checkins
                DELETE FROM user_habit_log_checkins h
                 WHERE h.course_id = 'personality_dev'
                   AND EXISTS (
                       SELECT 1 FROM user_habit_log_checkins h2
                        WHERE h2.user_id = h.user_id
                          AND h2.course_id = 'empathy-growth-mindset'
                          AND h2.log_type = h.log_type
                          AND h2.day_number = h.day_number
                   );
                UPDATE user_habit_log_checkins
                   SET course_id = 'empathy-growth-mindset'
                 WHERE course_id = 'personality_dev';

                -- Update historical posts and XP events
                UPDATE posts SET course_id = 'empathy-growth-mindset' WHERE course_id = 'personality_dev';
                UPDATE xp_events SET course_id = 'empathy-growth-mindset' WHERE course_id = 'personality_dev';

                -- Remove legacy course row
                DELETE FROM courses WHERE id = 'personality_dev';
            END IF;
        END $$;
    """)


def downgrade() -> None:
    # Course rename is forward-only; keep empathy-growth-mindset intact.
    pass
