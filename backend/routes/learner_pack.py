# ============================================================
# Learner Pack Routes — SWAYAM Plus Modular Course System
# ============================================================
# Provides endpoints for:
# 1. Course overview with weekly breakdown & learner pack progress
# 2. Detailed tutorial content (Reading, Notebook activity, Reflection prompt, Quiz)
# 3. Reading completion handler
# 4. Student reflection submissions (with automated XP & assignment_done flag)
# 5. Interactive 5-question Quiz submissions & explanations (with automated XP & practiced flag)
# 6. Multi-day Habit Log check-ins (Emotion, Belief, Empathy, Breathing, Portfolio)
# ============================================================

import uuid
from datetime import datetime, timezone, date
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from database import get_db
from dependencies import get_current_user
from models import User, Course, Tutorial, UserTutorial
from models.learner_pack import (
    TutorialContent,
    QuizQuestion,
    UserReflection,
    UserQuizAttempt,
    UserHabitLogCheckin,
)
from models.xp_event import XPEvent
from services.xp import recompute_tutorial_xp, recalc_level

router = APIRouter(prefix="/api/learner-pack", tags=["learner_pack"])


# ------------------------------------------------------------
# Pydantic Schemas
# ------------------------------------------------------------

class ReflectionSubmitRequest(BaseModel):
    reflection_text: str = Field(..., min_length=15, description="3-5 sentence personal reflection")


class QuizSubmitRequest(BaseModel):
    answers: Dict[str, str] = Field(..., description="Mapping of question_number (as string) to selected option (e.g. {'1': 'A', '2': 'C'})")


class HabitLogCheckinRequest(BaseModel):
    course_id: str
    log_type: str = Field(..., description="emotion | belief | empathy | breathing | portfolio")
    day_number: int = Field(..., ge=1, le=14, description="Day number of the log (1-7 or up to 14)")
    checkin_date: date
    summary_reflection: Optional[str] = Field(None, description="End of log reflection text")


# ------------------------------------------------------------
# Helper: Get or Create UserTutorial
# ------------------------------------------------------------

async def _get_or_create_user_tutorial(db: AsyncSession, user_id: uuid.UUID, tutorial_id: uuid.UUID) -> UserTutorial:
    result = await db.execute(
        select(UserTutorial)
        .options(selectinload(UserTutorial.tutorial))
        .filter_by(user_id=user_id, tutorial_id=tutorial_id)
    )
    ut = result.scalars().first()
    if not ut:
        ut = UserTutorial(
            user_id=user_id,
            tutorial_id=tutorial_id,
            status="not_started",
            watched=False,
            practiced=False,
            assignment_done=False,
            forum_asked=False,
            forum_answered=False,
            xp_earned=0,
        )
        db.add(ut)
        await db.flush()
        # Reload with relationship
        result = await db.execute(
            select(UserTutorial)
            .options(selectinload(UserTutorial.tutorial))
            .filter_by(user_id=user_id, tutorial_id=tutorial_id)
        )
        ut = result.scalars().first()
    return ut


# ------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------

@router.get("/course/{course_id}/overview")
async def get_course_overview(
    course_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns high-level structure of a Learner Pack course grouped by week,
    including completion status, reflection status, and quiz scores.
    """
    # 1. Fetch course
    c_res = await db.execute(select(Course).filter_by(id=course_id))
    course = c_res.scalars().first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # 2. Fetch all tutorials for this course
    t_res = await db.execute(
        select(Tutorial)
        .options(selectinload(Tutorial.learner_pack_content))
        .filter_by(course_id=course_id)
        .order_by(Tutorial.tutorial_number)
    )
    tutorials = t_res.scalars().all()
    tut_ids = [t.id for t in tutorials]

    # 3. Fetch user tutorials
    ut_res = await db.execute(
        select(UserTutorial).filter(
            UserTutorial.user_id == user.id,
            UserTutorial.tutorial_id.in_(tut_ids) if tut_ids else False
        )
    )
    user_tuts = {ut.tutorial_id: ut for ut in ut_res.scalars().all()}

    # 4. Fetch user reflections
    ref_res = await db.execute(
        select(UserReflection).filter(
            UserReflection.user_id == user.id,
            UserReflection.tutorial_id.in_(tut_ids) if tut_ids else False
        )
    )
    user_refs = {r.tutorial_id: r for r in ref_res.scalars().all()}

    # 5. Fetch user quiz attempts
    qa_res = await db.execute(
        select(UserQuizAttempt).filter(
            UserQuizAttempt.user_id == user.id,
            UserQuizAttempt.tutorial_id.in_(tut_ids) if tut_ids else False
        )
    )
    user_quizzes = {q.tutorial_id: q for q in qa_res.scalars().all()}

    # 6. Build response
    tutorial_list = []
    for tut in tutorials:
        ut = user_tuts.get(tut.id)
        ref = user_refs.get(tut.id)
        quiz = user_quizzes.get(tut.id)
        content = tut.learner_pack_content[0] if tut.learner_pack_content else None

        tutorial_list.append({
            "id": str(tut.id),
            "number": tut.tutorial_number,
            "title": tut.title,
            "week": content.week_number if content else 1,
            "hasContent": content is not None,
            "readingTitle": content.reading_title if content else None,
            "readingTimeMinutes": content.reading_time_minutes if content else 15,
            "userProgress": {
                "watched": ut.watched if ut else False,
                "readingCompleted": ut.watched if ut else False,
                "reflectionSubmitted": ref is not None or (ut.assignment_done if ut else False),
                "reflectionWordCount": ref.word_count if ref else 0,
                "quizPassed": quiz.passed if quiz else (ut.practiced if ut else False),
                "quizScore": quiz.score if quiz else None,
                "status": ut.status if ut else "not_started",
                "xpEarned": ut.xp_earned if ut else 0,
            }
        })

    # Habit log milestones for SWAYAM Plus
    habit_milestones = [
        {"week": 3, "logType": "emotion", "title": "7-Day Emotion Log", "days": 7},
        {"week": 6, "logType": "belief", "title": "7-Day Belief Log", "days": 7},
        {"week": 7, "logType": "empathy", "title": "7-Day Empathy Log", "days": 7},
        {"week": 10, "logType": "breathing", "title": "7-Day Mindful Breathing Log", "days": 7},
        {"week": 12, "logType": "portfolio", "title": "Personal Growth Portfolio", "days": 1},
    ]

    return {
        "courseId": course.id,
        "title": course.title,
        "uiLayout": course.ui_layout,
        "totalWeeks": 12,
        "tutorials": tutorial_list,
        "habitMilestones": habit_milestones,
    }


@router.get("/tutorials/{tutorial_id}")
async def get_tutorial_content(
    tutorial_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns full learner pack content for a specific tutorial,
    including reading markdown, Try It activity prompt, reflection prompt,
    and 5 quiz questions. Correct answers and explanations are only included
    if the student has already submitted a quiz attempt.
    """
    try:
        tut_uuid = uuid.UUID(tutorial_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid tutorial ID")

    # Fetch tutorial
    t_res = await db.execute(select(Tutorial).filter_by(id=tut_uuid))
    tutorial = t_res.scalars().first()
    if not tutorial:
        raise HTTPException(status_code=404, detail="Tutorial not found")

    # Fetch learner pack content
    c_res = await db.execute(select(TutorialContent).filter_by(tutorial_id=tut_uuid))
    content = c_res.scalars().first()

    # Fetch quiz questions
    q_res = await db.execute(
        select(QuizQuestion)
        .filter_by(tutorial_id=tut_uuid)
        .order_by(QuizQuestion.question_number)
    )
    quiz_questions = q_res.scalars().all()

    # Fetch user progress
    ut = await _get_or_create_user_tutorial(db, user.id, tut_uuid)

    # Fetch user reflection
    ref_res = await db.execute(select(UserReflection).filter_by(user_id=user.id, tutorial_id=tut_uuid))
    user_reflection = ref_res.scalars().first()

    # Fetch user quiz attempt
    qa_res = await db.execute(select(UserQuizAttempt).filter_by(user_id=user.id, tutorial_id=tut_uuid))
    user_attempt = qa_res.scalars().first()

    # Format questions: withhold correct_option & explanation unless attempted
    has_attempted_quiz = user_attempt is not None
    formatted_questions = []
    for q in quiz_questions:
        q_data = {
            "id": str(q.id),
            "questionNumber": q.question_number,
            "questionText": q.question_text,
            "options": q.options,
        }
        if has_attempted_quiz:
            q_data["correctOption"] = q.correct_option
            q_data["explanation"] = q.explanation
            if user_attempt and str(q.question_number) in user_attempt.submitted_answers:
                q_data["selectedOption"] = user_attempt.submitted_answers[str(q.question_number)]
        formatted_questions.append(q_data)

    return {
        "tutorialId": str(tutorial.id),
        "tutorialNumber": tutorial.tutorial_number,
        "title": tutorial.title,
        "courseId": tutorial.course_id,
        "content": {
            "weekNumber": content.week_number if content else 1,
            "readingTitle": content.reading_title if content else f"Reading for {tutorial.title}",
            "readingMarkdown": content.reading_markdown if content else "Reading content coming soon.",
            "readingTimeMinutes": content.reading_time_minutes if content else 15,
            "tryItInstructions": content.try_it_instructions if content else "Complete the notebook activity as instructed in the video.",
            "reflectionPrompt": content.reflection_prompt if content else "Write 3-5 sentences reflecting on this tutorial.",
            "reflectionMinSentences": content.reflection_min_sentences if content else 3,
            "keyTerms": content.key_terms if content else [],
            "readMore": content.read_more if content else [],
        } if content else None,
        "quiz": {
            "hasAttempted": has_attempted_quiz,
            "score": user_attempt.score if user_attempt else None,
            "totalQuestions": len(quiz_questions),
            "passed": user_attempt.passed if user_attempt else False,
            "submittedAt": user_attempt.submitted_at.isoformat() if user_attempt else None,
            "questions": formatted_questions,
        },
        "userReflection": {
            "reflectionText": user_reflection.reflection_text,
            "wordCount": user_reflection.word_count,
            "submittedAt": user_reflection.submitted_at.isoformat(),
        } if user_reflection else None,
        "userTutorial": ut.to_api_dict(),
    }


@router.post("/tutorials/{tutorial_id}/reading-complete")
async def mark_reading_complete(
    tutorial_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Marks the reading/video portion as completed (watched=True) and awards 10 XP.
    """
    try:
        tut_uuid = uuid.UUID(tutorial_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid tutorial ID")

    ut = await _get_or_create_user_tutorial(db, user.id, tut_uuid)
    if not ut.watched:
        ut.watched = True
        xp_gained = recompute_tutorial_xp(ut)
        if xp_gained != 0:
            user.xp_total += xp_gained
            db.add(XPEvent(
                user_id=user.id,
                source_type="tutorial_completion",
                source_id=str(tut_uuid),
                xp_delta=xp_gained,
                course_id=ut.tutorial.course_id if ut.tutorial else None,
            ))
            recalc_level(user)
        await db.commit()

    return {"success": True, "userTutorial": ut.to_api_dict()}


@router.post("/tutorials/{tutorial_id}/activity-complete")
async def mark_activity_complete(
    tutorial_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Marks the private notebook exercise as completed (minitask_opted = True)
    and awards 5 XP if not already awarded.
    """
    try:
        tut_uuid = uuid.UUID(tutorial_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid tutorial ID")

    ut = await _get_or_create_user_tutorial(db, user.id, tut_uuid)
    if not ut.minitask_opted:
        ut.minitask_opted = True
        user.xp_total += 5
        db.add(XPEvent(
            user_id=user.id,
            source_type="activity_completion",
            source_id=str(tut_uuid),
            xp_delta=5,
            course_id=ut.tutorial.course_id if ut.tutorial else None,
        ))
        recalc_level(user)
        await db.commit()

    return {"success": True, "userTutorial": ut.to_api_dict()}


@router.post("/tutorials/{tutorial_id}/reflection")
async def submit_reflection(
    tutorial_id: str,
    body: ReflectionSubmitRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Saves student's 3-5 sentence reflection, sets assignment_done = True,
    and awards XP accordingly.
    """
    try:
        tut_uuid = uuid.UUID(tutorial_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid tutorial ID")

    # Word count estimation
    text = body.reflection_text.strip()
    words = len(text.split())
    if words < 10:
        raise HTTPException(status_code=400, detail="Please write a complete reflection of at least 3 sentences.")

    # 1. Upsert UserReflection
    ref_res = await db.execute(
        select(UserReflection).filter_by(user_id=user.id, tutorial_id=tut_uuid)
    )
    user_ref = ref_res.scalars().first()
    if user_ref:
        user_ref.reflection_text = text
        user_ref.word_count = words
        user_ref.submitted_at = datetime.now(timezone.utc)
    else:
        user_ref = UserReflection(
            id=uuid.uuid4(),
            user_id=user.id,
            tutorial_id=tut_uuid,
            reflection_text=text,
            word_count=words,
            submitted_at=datetime.now(timezone.utc),
        )
        db.add(user_ref)

    # 2. Update UserTutorial -> assignment_done = True
    ut = await _get_or_create_user_tutorial(db, user.id, tut_uuid)
    ut.assignment_done = True

    # Recompute XP
    xp_gained = recompute_tutorial_xp(ut)
    if xp_gained != 0:
        user.xp_total += xp_gained
        db.add(XPEvent(
            user_id=user.id,
            source_type="learner_pack_reflection",
            source_id=str(tut_uuid),
            xp_delta=xp_gained,
            course_id=ut.tutorial.course_id if ut.tutorial else None,
        ))
        recalc_level(user)

    await db.commit()

    return {
        "success": True,
        "reflection": {
            "reflectionText": user_ref.reflection_text,
            "wordCount": user_ref.word_count,
            "submittedAt": user_ref.submitted_at.isoformat(),
        },
        "userTutorial": ut.to_api_dict(),
        "xpGained": xp_gained,
    }


@router.post("/tutorials/{tutorial_id}/quiz")
async def submit_quiz(
    tutorial_id: str,
    body: QuizSubmitRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Evaluates 5 submitted answers against QuizQuestions, calculates score,
    marks practiced = True and status = 'completed' if passed,
    and returns full questions with explanations.
    """
    try:
        tut_uuid = uuid.UUID(tutorial_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid tutorial ID")

    # Fetch all quiz questions for tutorial
    q_res = await db.execute(
        select(QuizQuestion)
        .filter_by(tutorial_id=tut_uuid)
        .order_by(QuizQuestion.question_number)
    )
    questions = q_res.scalars().all()
    if not questions:
        raise HTTPException(status_code=404, detail="No quiz questions found for this tutorial")

    # Score calculation
    correct_count = 0
    results = []
    for q in questions:
        key = str(q.question_number)
        selected = body.answers.get(key, "").strip().upper()
        is_correct = (selected == q.correct_option.strip().upper())
        if is_correct:
            correct_count += 1

        results.append({
            "id": str(q.id),
            "questionNumber": q.question_number,
            "questionText": q.question_text,
            "options": q.options,
            "selectedOption": selected,
            "correctOption": q.correct_option,
            "isCorrect": is_correct,
            "explanation": q.explanation,
        })

    passed = correct_count >= 3  # Pass mark: 3 out of 5 (60%)

    # Upsert UserQuizAttempt
    qa_res = await db.execute(select(UserQuizAttempt).filter_by(user_id=user.id, tutorial_id=tut_uuid))
    attempt = qa_res.scalars().first()
    if attempt:
        attempt.score = correct_count
        attempt.total_questions = len(questions)
        attempt.submitted_answers = body.answers
        attempt.passed = passed
        attempt.submitted_at = datetime.now(timezone.utc)
    else:
        attempt = UserQuizAttempt(
            id=uuid.uuid4(),
            user_id=user.id,
            tutorial_id=tut_uuid,
            score=correct_count,
            total_questions=len(questions),
            submitted_answers=body.answers,
            passed=passed,
            submitted_at=datetime.now(timezone.utc),
        )
        db.add(attempt)

    # Update UserTutorial -> practiced = True, status = "completed"
    ut = await _get_or_create_user_tutorial(db, user.id, tut_uuid)
    if passed or attempt.score > 0:
        ut.practiced = True
        ut.status = "completed"

    xp_gained = recompute_tutorial_xp(ut)
    if xp_gained != 0:
        user.xp_total += xp_gained
        db.add(XPEvent(
            user_id=user.id,
            source_type="learner_pack_quiz",
            source_id=str(tut_uuid),
            xp_delta=xp_gained,
            course_id=ut.tutorial.course_id if ut.tutorial else None,
        ))
        recalc_level(user)

    await db.commit()

    return {
        "score": correct_count,
        "totalQuestions": len(questions),
        "passed": passed,
        "results": results,
        "userTutorial": ut.to_api_dict(),
        "xpGained": xp_gained,
    }


@router.get("/habit-logs/{course_id}")
async def get_habit_logs(
    course_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns all habit log check-ins for this user in the specified course.
    """
    res = await db.execute(
        select(UserHabitLogCheckin)
        .filter_by(user_id=user.id, course_id=course_id)
        .order_by(UserHabitLogCheckin.day_number)
    )
    checkins = res.scalars().all()

    grouped: Dict[str, list] = {
        "emotion": [],
        "belief": [],
        "empathy": [],
        "breathing": [],
        "portfolio": [],
    }

    for c in checkins:
        if c.log_type in grouped:
            grouped[c.log_type].append({
                "id": str(c.id),
                "dayNumber": c.day_number,
                "checkinDate": c.checkin_date.isoformat(),
                "summaryReflection": c.summary_reflection,
                "summarySubmittedAt": c.summary_submitted_at.isoformat() if c.summary_submitted_at else None,
            })

    return {"courseId": course_id, "logs": grouped}


@router.post("/habit-logs/checkin")
async def record_habit_checkin(
    body: HabitLogCheckinRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Records a daily check-in or end-of-log reflection for a habit milestone.
    """
    valid_logs = {"emotion", "belief", "empathy", "breathing", "portfolio"}
    if body.log_type not in valid_logs:
        raise HTTPException(status_code=400, detail=f"Invalid log_type. Must be one of {valid_logs}")

    # Upsert checkin
    res = await db.execute(
        select(UserHabitLogCheckin).filter_by(
            user_id=user.id,
            course_id=body.course_id,
            log_type=body.log_type,
            day_number=body.day_number,
        )
    )
    checkin = res.scalars().first()
    now_dt = datetime.now(timezone.utc)

    if checkin:
        checkin.checkin_date = body.checkin_date
        if body.summary_reflection:
            checkin.summary_reflection = body.summary_reflection
            checkin.summary_submitted_at = now_dt
    else:
        checkin = UserHabitLogCheckin(
            id=uuid.uuid4(),
            user_id=user.id,
            course_id=body.course_id,
            log_type=body.log_type,
            day_number=body.day_number,
            checkin_date=body.checkin_date,
            summary_reflection=body.summary_reflection,
            summary_submitted_at=now_dt if body.summary_reflection else None,
        )
        db.add(checkin)

    await db.commit()

    return {
        "success": True,
        "checkin": {
            "id": str(checkin.id),
            "logType": checkin.log_type,
            "dayNumber": checkin.day_number,
            "checkinDate": checkin.checkin_date.isoformat(),
            "summaryReflection": checkin.summary_reflection,
            "summarySubmittedAt": checkin.summary_submitted_at.isoformat() if checkin.summary_submitted_at else None,
        }
    }
