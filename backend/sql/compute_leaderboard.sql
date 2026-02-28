-- ============================================================
-- compute_leaderboard_weekly()
-- 
-- Snapshots the weekly leaderboard into leaderboard_weekly.
-- Reads xp_events from the past 7 days, aggregates by user,
-- ranks them, and inserts into the snapshot table.
--
-- Run every Monday at 00:05 via scheduler.
-- ============================================================

CREATE OR REPLACE FUNCTION compute_leaderboard_weekly()
RETURNS void AS $$
DECLARE
    v_week_start DATE;
BEGIN
    -- Week starts on the most recent Monday
    v_week_start := date_trunc('week', CURRENT_DATE)::DATE;

    -- 1. Delete existing rows for this week (idempotent re-run)
    DELETE FROM leaderboard_weekly WHERE week_start = v_week_start;

    -- 2. Insert overall leaderboard (course_id = '__all__')
    INSERT INTO leaderboard_weekly (week_start, course_id, user_id, xp_week, rank)
    SELECT
        v_week_start,
        '__all__',
        xe.user_id,
        COALESCE(SUM(xe.xp_delta), 0) AS xp_week,
        ROW_NUMBER() OVER (ORDER BY COALESCE(SUM(xe.xp_delta), 0) DESC) AS rank
    FROM xp_events xe
    WHERE xe.created_at >= v_week_start
      AND xe.created_at < v_week_start + INTERVAL '7 days'
    GROUP BY xe.user_id;

    -- 3. Update users.xp_last_week from the snapshot
    UPDATE users u
    SET xp_last_week = COALESCE(lw.xp_week, 0)
    FROM leaderboard_weekly lw
    WHERE lw.user_id = u.id
      AND lw.week_start = v_week_start
      AND lw.course_id = '__all__';

    -- Reset xp_last_week to 0 for users with no activity
    UPDATE users
    SET xp_last_week = 0
    WHERE id NOT IN (
        SELECT user_id FROM leaderboard_weekly
        WHERE week_start = v_week_start AND course_id = '__all__'
    );

END;
$$ LANGUAGE plpgsql;
