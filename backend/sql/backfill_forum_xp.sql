BEGIN;
-- docker compose exec -T postgres psql -U <your_actual_username> -d <your_actual_db> < backend/sql/backfill_forum_xp.sql

-- 1. Create a temporary table to hold the missing XP calculations
CREATE TEMP TABLE temp_missing_xp AS
SELECT 
    user_id,
    tutorial_id,
    (CASE WHEN forum_asked THEN 5 ELSE 0 END) + 
    (CASE WHEN forum_answered THEN 10 ELSE 0 END) AS missing_xp
FROM user_tutorials
WHERE forum_asked = true OR forum_answered = true;

-- 2. Update user_tutorials xp_earned
UPDATE user_tutorials ut
SET xp_earned = ut.xp_earned + tmx.missing_xp
FROM temp_missing_xp tmx
WHERE ut.user_id = tmx.user_id AND ut.tutorial_id = tmx.tutorial_id;

-- 3. Update users xp_total
UPDATE users u
SET xp_total = u.xp_total + (
    SELECT SUM(missing_xp) 
    FROM temp_missing_xp 
    WHERE temp_missing_xp.user_id = u.id
)
WHERE id IN (SELECT DISTINCT user_id FROM temp_missing_xp);

-- 4. Insert XP Events so it counts towards the weekly leaderboard
INSERT INTO xp_events (user_id, source_type, source_id, xp_delta, created_at)
SELECT 
    user_id,
    'tutorial_completion_backfill',
    tutorial_id::varchar,
    missing_xp,
    NOW()
FROM temp_missing_xp;

-- 5. Drop temp table
DROP TABLE temp_missing_xp;

COMMIT;
