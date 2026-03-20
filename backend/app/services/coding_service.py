"""
Service layer for coding challenges and courses.

Handles business logic: XP calculation, submission validation, progress tracking,
course enrollment, lesson completion.
"""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.coding_repo import CodingRepository, CourseRepository
from app.models.coding import CodingTopic, CodingChallenge, CodingSubmission
from app.schemas.coding import (
    TopicWithProgress,
    ChallengeListItem,
    ChallengeDetail,
    TestCasePublic,
    SubmissionCreate,
    SubmissionResponse,
    CodingStats,
    CourseWithProgress,
    LessonListItem,
    LessonDetail,
    LessonCompleteResponse,
)


class CodingServiceError(Exception):
    pass


class CodingService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = CodingRepository(db)

    # -----------------------------------------------------------------------
    # Topics with progress
    # -----------------------------------------------------------------------

    async def list_topics_with_progress(
        self, student_id: int
    ) -> list[TopicWithProgress]:
        topics = await self.repo.list_topics(active_only=True)
        if not topics:
            return []

        topic_ids = [t.id for t in topics]
        total_counts = await self.repo.count_challenges_by_topic(topic_ids)
        solved_counts = await self.repo.get_solved_count_by_topic(student_id, topic_ids)

        result = []
        for t in topics:
            result.append(TopicWithProgress(
                id=t.id,
                title=t.title,
                title_kk=t.title_kk,
                slug=t.slug,
                description=t.description,
                description_kk=t.description_kk,
                sort_order=t.sort_order,
                icon=t.icon,
                grade_level=t.grade_level,
                is_active=t.is_active,
                total_challenges=total_counts.get(t.id, 0),
                solved_challenges=solved_counts.get(t.id, 0),
            ))
        return result

    # -----------------------------------------------------------------------
    # Challenges list with student status
    # -----------------------------------------------------------------------

    async def list_challenges(
        self, topic_slug: str, student_id: int
    ) -> list[ChallengeListItem]:
        topic = await self.repo.get_topic_by_slug(topic_slug)
        if not topic:
            raise CodingServiceError("Topic not found")

        challenges = await self.repo.list_challenges_by_topic(topic.id)
        if not challenges:
            return []

        ch_ids = [c.id for c in challenges]
        solved = await self.repo.get_solved_challenge_ids(student_id, ch_ids)
        attempted = await self.repo.get_attempted_challenge_ids(student_id, ch_ids)

        result = []
        for c in challenges:
            if c.id in solved:
                st = "solved"
            elif c.id in attempted:
                st = "attempted"
            else:
                st = "not_started"
            result.append(ChallengeListItem(
                id=c.id,
                title=c.title,
                title_kk=c.title_kk,
                difficulty=c.difficulty,
                points=c.points,
                sort_order=c.sort_order,
                status=st,
            ))
        return result

    # -----------------------------------------------------------------------
    # Challenge detail
    # -----------------------------------------------------------------------

    async def get_challenge_detail(
        self, challenge_id: int, student_id: int
    ) -> ChallengeDetail:
        ch = await self.repo.get_challenge_by_id(challenge_id)
        if not ch or not ch.is_active:
            raise CodingServiceError("Challenge not found")

        # Determine status
        has_passed = await self.repo.has_passed(student_id, challenge_id)
        if has_passed:
            status = "solved"
        else:
            attempts = await self.repo.get_attempts_count(student_id, challenge_id)
            status = "attempted" if attempts > 0 else "not_started"

        # Best submission
        best = await self.repo.get_best_submission(student_id, challenge_id)
        best_resp = SubmissionResponse.model_validate(best) if best else None

        # Build public test cases — hide expected_output for hidden tests
        public_tests = []
        for tc in (ch.test_cases or []):
            if tc.get("is_hidden"):
                public_tests.append(TestCasePublic(
                    input="",
                    expected_output="",
                    description=tc.get("description", "Скрытый тест"),
                    is_hidden=True,
                ))
            else:
                public_tests.append(TestCasePublic(
                    input=tc.get("input", ""),
                    expected_output=tc.get("expected_output", ""),
                    description=tc.get("description"),
                    is_hidden=False,
                ))

        return ChallengeDetail(
            id=ch.id,
            topic_id=ch.topic_id,
            title=ch.title,
            title_kk=ch.title_kk,
            description=ch.description,
            description_kk=ch.description_kk,
            difficulty=ch.difficulty,
            points=ch.points,
            starter_code=ch.starter_code,
            hints=ch.hints or [],
            hints_kk=ch.hints_kk or [],
            test_cases=public_tests,
            time_limit_ms=ch.time_limit_ms,
            status=status,
            best_submission=best_resp,
        )

    # -----------------------------------------------------------------------
    # Submit solution
    # -----------------------------------------------------------------------

    async def submit_solution(
        self,
        challenge_id: int,
        student_id: int,
        school_id: int,
        data: SubmissionCreate,
    ) -> SubmissionResponse:
        ch = await self.repo.get_challenge_by_id(challenge_id)
        if not ch or not ch.is_active:
            raise CodingServiceError("Challenge not found")

        # Determine status
        all_passed = data.tests_passed == data.tests_total
        if data.error_message:
            submission_status = "error"
        elif all_passed:
            submission_status = "passed"
        else:
            submission_status = "failed"

        # Attempt number
        attempt_number = await self.repo.get_attempts_count(student_id, challenge_id) + 1

        # XP: award only on first successful solve
        xp_earned = 0
        if submission_status == "passed":
            already_solved = await self.repo.has_passed(student_id, challenge_id)
            if not already_solved:
                xp_earned = ch.points

        sub = await self.repo.create_submission(
            student_id=student_id,
            school_id=school_id,
            challenge_id=challenge_id,
            code=data.code,
            status=submission_status,
            tests_passed=data.tests_passed,
            tests_total=data.tests_total,
            execution_time_ms=data.execution_time_ms,
            error_message=data.error_message,
            attempt_number=attempt_number,
            xp_earned=xp_earned,
        )
        await self.db.commit()

        # Gamification hook: award XP + streak + achievements + daily quest
        if xp_earned > 0:
            from app.services.gamification_service import GamificationService
            gam = GamificationService(self.db)
            await gam.on_coding_challenge_solved(
                student_id=student_id,
                school_id=school_id,
                challenge_id=challenge_id,
                xp_earned=xp_earned,
                difficulty=ch.difficulty,
                execution_time_ms=data.execution_time_ms,
            )
            await self.db.commit()

        return SubmissionResponse.model_validate(sub)

    # -----------------------------------------------------------------------
    # Submissions history
    # -----------------------------------------------------------------------

    async def list_submissions(
        self, challenge_id: int, student_id: int
    ) -> list[SubmissionResponse]:
        subs = await self.repo.list_submissions(student_id, challenge_id)
        return [SubmissionResponse.model_validate(s) for s in subs]

    # -----------------------------------------------------------------------
    # Stats
    # -----------------------------------------------------------------------

    async def get_stats(self, student_id: int) -> CodingStats:
        totals = await self.repo.get_student_total_stats(student_id)
        topics = await self.list_topics_with_progress(student_id)
        return CodingStats(
            total_solved=totals["total_solved"],
            total_attempts=totals["total_attempts"],
            total_xp=totals["total_xp"],
            topics_progress=topics,
        )


# ===========================================================================
# Course Service (Learning Paths)
# ===========================================================================


class CourseService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = CourseRepository(db)
        self.coding_repo = CodingRepository(db)

    # -----------------------------------------------------------------------
    # List courses with progress
    # -----------------------------------------------------------------------

    async def list_courses_with_progress(
        self, student_id: int
    ) -> list[CourseWithProgress]:
        courses = await self.repo.list_courses(active_only=True)
        if not courses:
            return []

        course_ids = [c.id for c in courses]
        progress_map = await self.repo.get_all_progress(student_id, course_ids)

        result = []
        for c in courses:
            p = progress_map.get(c.id)
            result.append(CourseWithProgress(
                id=c.id,
                title=c.title,
                title_kk=c.title_kk,
                description=c.description,
                description_kk=c.description_kk,
                slug=c.slug,
                grade_level=c.grade_level,
                total_lessons=c.total_lessons,
                estimated_hours=c.estimated_hours,
                sort_order=c.sort_order,
                icon=c.icon,
                is_active=c.is_active,
                completed_lessons=p.completed_lessons if p else 0,
                last_lesson_id=p.last_lesson_id if p else None,
                started=p is not None,
                completed=p.completed_at is not None if p else False,
            ))
        return result

    # -----------------------------------------------------------------------
    # List lessons with completion status
    # -----------------------------------------------------------------------

    async def list_lessons(
        self, course_slug: str, student_id: int
    ) -> list[LessonListItem]:
        course = await self.repo.get_course_by_slug(course_slug)
        if not course:
            raise CodingServiceError("Course not found")

        lessons = await self.repo.list_lessons(course.id)
        if not lessons:
            return []

        completed_ids = await self.repo.get_completed_lesson_ids(student_id, course.id)

        result = []
        for lesson in lessons:
            result.append(LessonListItem(
                id=lesson.id,
                title=lesson.title,
                title_kk=lesson.title_kk,
                sort_order=lesson.sort_order,
                has_challenge=lesson.challenge_id is not None,
                challenge_id=lesson.challenge_id,
                is_completed=lesson.id in completed_ids,
            ))
        return result

    # -----------------------------------------------------------------------
    # Lesson detail
    # -----------------------------------------------------------------------

    async def get_lesson_detail(
        self, lesson_id: int, student_id: int
    ) -> LessonDetail:
        lesson = await self.repo.get_lesson_by_id(lesson_id)
        if not lesson or not lesson.is_active:
            raise CodingServiceError("Lesson not found")

        completed_ids = await self.repo.get_completed_lesson_ids(
            student_id, lesson.course_id
        )

        # Optionally include challenge detail
        challenge_detail = None
        if lesson.challenge_id:
            coding_svc = CodingService(self.db)
            try:
                challenge_detail = await coding_svc.get_challenge_detail(
                    lesson.challenge_id, student_id
                )
            except CodingServiceError:
                pass  # challenge not found/inactive — skip

        return LessonDetail(
            id=lesson.id,
            course_id=lesson.course_id,
            title=lesson.title,
            title_kk=lesson.title_kk,
            sort_order=lesson.sort_order,
            theory_content=lesson.theory_content,
            theory_content_kk=lesson.theory_content_kk,
            starter_code=lesson.starter_code,
            challenge_id=lesson.challenge_id,
            challenge=challenge_detail,
            is_completed=lesson.id in completed_ids,
        )

    # -----------------------------------------------------------------------
    # Complete a lesson
    # -----------------------------------------------------------------------

    async def complete_lesson(
        self, lesson_id: int, student_id: int, school_id: int = 0
    ) -> LessonCompleteResponse:
        lesson = await self.repo.get_lesson_by_id(lesson_id)
        if not lesson or not lesson.is_active:
            raise CodingServiceError("Lesson not found")

        course = await self.repo.get_course_by_id(lesson.course_id)
        if not course:
            raise CodingServiceError("Course not found")

        # Get all active lessons for this course to calculate position
        all_lessons = await self.repo.list_lessons(course.id)
        lesson_ids = [l.id for l in all_lessons]

        if lesson.id not in lesson_ids:
            raise CodingServiceError("Lesson not in course")

        # Current progress
        completed_ids = await self.repo.get_completed_lesson_ids(
            student_id, course.id
        )

        # Add this lesson if not already completed
        if lesson.id not in completed_ids:
            completed_ids.add(lesson.id)

        # Count completed (based on order — only contiguous from start)
        completed_count = 0
        for l in all_lessons:
            if l.id in completed_ids:
                completed_count += 1
            else:
                break

        course_completed = completed_count >= len(all_lessons)
        completed_at = datetime.now(timezone.utc) if course_completed else None

        await self.repo.upsert_progress(
            student_id=student_id,
            course_id=course.id,
            last_lesson_id=lesson.id,
            completed_lessons=completed_count,
            completed_at=completed_at,
        )
        await self.db.commit()

        # Gamification hook: award XP when full course is completed
        if course_completed and school_id:
            from app.services.gamification_service import GamificationService
            gam = GamificationService(self.db)
            await gam.on_course_completed(
                student_id=student_id,
                school_id=school_id,
                course_id=course.id,
            )
            await self.db.commit()

        return LessonCompleteResponse(
            lesson_id=lesson.id,
            course_id=course.id,
            completed_lessons=completed_count,
            total_lessons=len(all_lessons),
            course_completed=course_completed,
        )
