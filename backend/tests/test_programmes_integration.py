import sys
import os

# Ensure backend root is on sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SyncSessionLocal
from models.programme import Programme, ProgrammeCourse
from models.course import Course, UserCourse
from models.user import User
from models.batch import Batch
from models.college_course import CollegeCourse

def test_programmes_and_courses():
    db = SyncSessionLocal()
    try:
        print("============================================================")
        print("VERIFYING PROGRAMMES & COURSES ABSTRACTION LAYER")
        print("============================================================")

        # 1. Verify Programmes Count and Names
        programmes = db.query(Programme).order_by(Programme.display_order).all()
        assert len(programmes) == 3, f"Expected 3 programmes, found {len(programmes)}"
        prog_ids = [p.id for p in programmes]
        assert "fdp" in prog_ids, "Missing FDP programme"
        assert "swayam_plus" in prog_ids, "Missing Swayam Plus programme"
        assert "ilw" in prog_ids, "Missing ILW programme"
        print("✅ Programmes list correct: fdp, swayam_plus, ilw.")

        # 2. Check FDP courses
        fdp_course_ids = [r.course_id for r in db.query(ProgrammeCourse).filter_by(programme_id="fdp").all()]
        expected_fdp = {"linux", "python", "latex", "scilab"}
        assert set(fdp_course_ids) == expected_fdp, f"FDP courses mismatch: {fdp_course_ids}"
        print(f"✅ FDP course mappings correct: {fdp_course_ids}")

        # 3. Check Swayam Plus courses
        sp_course_ids = [r.course_id for r in db.query(ProgrammeCourse).filter_by(programme_id="swayam_plus").all()]
        expected_sp = {"swayam_plus-linux", "swayam_plus-postgresql", "swayam_plus-ai", "swayam_plus-phd"}
        assert set(sp_course_ids) == expected_sp, f"Swayam Plus courses mismatch: {sp_course_ids}"
        print(f"✅ Swayam Plus course mappings correct: {sp_course_ids}")

        # 4. Check ILW courses
        ilw_course_ids = [r.course_id for r in db.query(ProgrammeCourse).filter_by(programme_id="ilw").all()]
        expected_ilw = {"ilw-webdev", "ilw-data_analytics", "ilw-iot"}
        assert set(ilw_course_ids) == expected_ilw, f"ILW courses mismatch: {ilw_course_ids}"
        print(f"✅ ILW course mappings correct: {ilw_course_ids}")

        # 5. Check Swayam Plus Linux Course Batch 1 Enrollment Count
        # It must contain the unique users from the CSV (2488) + mock users (20) = 2508
        sp_linux_batch1_count = db.query(UserCourse).filter_by(
            course_id="swayam_plus-linux",
            batch_id="swayam_plus-linux-2026-batch1"
        ).count()
        assert sp_linux_batch1_count == 2508, f"Expected 2508 enrollments in Swayam Plus Linux Batch 1, but found {sp_linux_batch1_count}"
        print(f"✅ Swayam Plus Linux Batch 1 contains exactly {sp_linux_batch1_count} enrollments.")

        # 6. Verify distinct users role counts
        student_count = db.query(User).filter_by(role="student").count()
        coord_count = db.query(User).filter_by(role="coordinator").count()
        admin_count = db.query(User).filter_by(role="admin").count()
        print(f"📊 Database Stats: {student_count} students, {coord_count} coordinators, {admin_count} admins.")

        print("============================================================")
        print("ALL TESTS PASSED SUCCESSFULLY!")
        print("============================================================")

    except AssertionError as e:
        print(f"❌ Verification failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    test_programmes_and_courses()
