"""
Service layer for coding challenges.

Handles business logic: XP calculation, submission validation, progress tracking.
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.coding_repo import CodingRepository
from app.models.coding import CodingTopic, CodingChallenge, CodingSubmission
from app.schemas.coding import (
    TopicWithProgress,
    ChallengeListItem,
    ChallengeDetail,
    TestCasePublic,
    SubmissionCreate,
    SubmissionResponse,
    CodingStats,
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
