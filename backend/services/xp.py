"""
Single source of truth for per-tutorial XP and level thresholds.

`UserTutorial.xp_earned` is ALWAYS the sum of XP_MAP over the tutorial's true boolean flags
— computed, never incremented. Both writers (routes/user.py update_tutorial and the forum
worker's _award_forum_xp) call recompute_tutorial_xp, so they can't clobber each other or
double-count. A consequence: forum XP counts once per tutorial per activity type (asked /
answered), not per post.
"""

# XP awarded per completed step of a tutorial.
XP_MAP = {
    "watched": 10,
    "practiced": 10,
    "assignment_done": 5,
    "forum_asked": 5,
    "forum_answered": 10,
}

# (xp_threshold, level), high to low.
_LEVELS = [(12000, 26), (7000, 21), (3500, 16), (1500, 11), (500, 6)]


def recompute_tutorial_xp(ut) -> int:
    """
    Set ut.xp_earned from its boolean flags and return the delta vs the previous value
    (to be applied to the user's global xp_total). Deterministic and idempotent: calling
    it again with the same flags returns 0.
    """
    old = ut.xp_earned or 0
    ut.xp_earned = sum(XP_MAP[col] for col in XP_MAP if getattr(ut, col) is True)
    return ut.xp_earned - old


def level_for_xp(xp_total: int) -> int:
    for threshold, level in _LEVELS:
        if xp_total >= threshold:
            return level
    return 1


def recalc_level(user) -> None:
    user.level = level_for_xp(user.xp_total)


def xp_for_next_level(xp_total: int) -> int:
    """The XP milestone for the next level up — used by the profile progress bar so it fills
    toward a real threshold and never exceeds 100%. Returns xp_total itself at max level.
    (The old 100*(level+1)^2 formula didn't match the discrete thresholds, so a level-1 user
    at 450 XP showed 112% without leveling up.)"""
    for threshold, _ in reversed(_LEVELS):  # ascending: 500, 1500, 3500, 7000, 12000
        if threshold > xp_total:
            return threshold
    return xp_total
