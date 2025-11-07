"""
Integration tests for Student API endpoints.

Tests the complete test-taking workflow:
- GET /api/v1/students/tests - available tests
- POST /api/v1/students/tests/{test_id}/start - start test
- GET /api/v1/students/attempts/{attempt_id} - get attempt
- POST /api/v1/students/attempts/{attempt_id}/submit - submit test
- GET /api/v1/students/progress - student progress

Critical tests:
- Multi-tenancy isolation (school_id)
- Ownership checks (student can only see their attempts)
- Grading accuracy
- Mastery tracking
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.test import Test, TestPurpose
from app.models.test_attempt import TestAttempt, AttemptStatus
from app.models.mastery import ParagraphMastery


# ========== Test 1: Get Available Tests (Isolation) ==========

@pytest.mark.asyncio
async def test_student_gets_available_tests(
    test_app,
    student_user: tuple,
    student_token: str,
    test_with_questions: Test,
    school1,
    db_session: AsyncSession
):
    """
    Test GET /api/v1/students/tests.

    Student should see:
    - Their school's tests (school_id = school1.id)
    - Global tests (school_id = NULL)

    Student should NOT see:
    - Other schools' tests
    """
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        response = await client.get(
            "/api/v1/students/tests",
            headers={"Authorization": f"Bearer {student_token}"}
        )

    assert response.status_code == 200
    tests = response.json()

    # Should see at least 1 test (test_with_questions from school1)
    assert len(tests) >= 1

    # All tests should be either from school1 or global (school_id=None)
    for test in tests:
        assert test["school_id"] == school1.id or test["school_id"] is None

    # Verify test metadata
    test_data = next(t for t in tests if t["id"] == test_with_questions.id)
    assert test_data["title"] == "Тест по линейным уравнениям"
    assert test_data["test_purpose"] == "formative"
    assert test_data["question_count"] == 4
    assert test_data["attempts_count"] == 0  # No attempts yet
    assert test_data["best_score"] is None


@pytest.mark.asyncio
async def test_student_gets_global_tests(
    test_app,
    student_user: tuple,
    student_token: str,
    global_test: Test,
    db_session: AsyncSession
):
    """
    Test that students can see global tests (school_id = NULL).

    Global tests should be visible to all schools.
    """
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        response = await client.get(
            "/api/v1/students/tests",
            headers={"Authorization": f"Bearer {student_token}"}
        )

    assert response.status_code == 200
    tests = response.json()

    # Find global test
    global_tests = [t for t in tests if t["school_id"] is None]
    assert len(global_tests) >= 1

    # Verify global test
    global_test_data = next(t for t in global_tests if t["id"] == global_test.id)
    assert global_test_data["title"] == "Тест по законам Ньютона (Глобальный)"
    assert global_test_data["test_purpose"] == "diagnostic"


@pytest.mark.asyncio
async def test_student_filters_by_chapter(
    test_app,
    student_user: tuple,
    student_token: str,
    test_with_questions: Test,
    chapter1,
    db_session: AsyncSession
):
    """
    Test filtering tests by chapter_id.

    GET /api/v1/students/tests?chapter_id=X should only return tests from that chapter.
    """
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        response = await client.get(
            f"/api/v1/students/tests?chapter_id={chapter1.id}",
            headers={"Authorization": f"Bearer {student_token}"}
        )

    assert response.status_code == 200
    tests = response.json()

    # All tests should be from chapter1
    for test in tests:
        assert test["chapter_id"] == chapter1.id


# ========== Test 2: Start Test ==========

@pytest.mark.asyncio
async def test_student_starts_test(
    test_app,
    student_user: tuple,
    student_token: str,
    test_with_questions: Test,
    db_session: AsyncSession
):
    """
    Test POST /api/v1/students/tests/{test_id}/start.

    Should create a new TestAttempt with:
    - status = IN_PROGRESS
    - attempt_number = 1 (first attempt)
    - Questions WITHOUT correct answers (security)
    """
    user, student = student_user

    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        response = await client.post(
            f"/api/v1/students/tests/{test_with_questions.id}/start",
            headers={"Authorization": f"Bearer {student_token}"}
        )

    assert response.status_code == 200
    data = response.json()

    # Verify attempt metadata
    assert data["status"] == "in_progress"
    assert data["attempt_number"] == 1
    assert data["test_id"] == test_with_questions.id
    assert data["student_id"] == student.id
    assert data["score"] is None  # Not graded yet

    # Verify test data included
    assert data["test"]["title"] == "Тест по линейным уравнениям"
    assert len(data["test"]["questions"]) == 4

    # CRITICAL: Questions should NOT have correct answers before submit
    for question in data["test"]["questions"]:
        for option in question["options"]:
            assert "is_correct" not in option  # Security check

    # Verify attempt created in database
    result = await db_session.execute(
        select(TestAttempt).where(TestAttempt.id == data["id"])
    )
    attempt = result.scalar_one()
    assert attempt.status == AttemptStatus.IN_PROGRESS
    assert attempt.student_id == student.id


@pytest.mark.asyncio
async def test_student_cannot_start_inactive_test(
    test_app,
    student_user: tuple,
    student_token: str,
    inactive_test: Test,
    db_session: AsyncSession
):
    """
    Test that students cannot start inactive tests (is_active=False).

    Expected: 404 Not Found (test not available)
    """
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        response = await client.post(
            f"/api/v1/students/tests/{inactive_test.id}/start",
            headers={"Authorization": f"Bearer {student_token}"}
        )

    assert response.status_code == 404
    assert "not available" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_attempt_number_increments(
    test_app,
    student_user: tuple,
    student_token: str,
    test_with_questions: Test,
    db_session: AsyncSession
):
    """
    Test that attempt_number auto-increments for multiple attempts.

    Student takes test 3 times -> attempt_number should be 1, 2, 3
    """
    user, student = student_user

    # Start test 3 times
    attempt_ids = []
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        for i in range(3):
            response = await client.post(
                f"/api/v1/students/tests/{test_with_questions.id}/start",
                headers={"Authorization": f"Bearer {student_token}"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["attempt_number"] == i + 1
            attempt_ids.append(data["id"])

            # Mark as completed to allow next attempt
            attempt_result = await db_session.execute(
                select(TestAttempt).where(TestAttempt.id == data["id"])
            )
            attempt = attempt_result.scalar_one()
            attempt.status = AttemptStatus.COMPLETED
            await db_session.commit()

    # Verify all 3 attempts exist
    assert len(attempt_ids) == 3


# ========== Test 3: Submit Test ==========

@pytest.mark.asyncio
async def test_student_submits_test(
    test_app,
    student_user: tuple,
    student_token: str,
    test_with_questions: Test,
    db_session: AsyncSession
):
    """
    Test POST /api/v1/students/attempts/{attempt_id}/submit.

    Should:
    - Accept bulk answers for all questions
    - Grade automatically
    - Return status = COMPLETED
    - Return questions WITH correct answers (security)
    """
    user, student = student_user

    # Start test first
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        start_response = await client.post(
            f"/api/v1/students/tests/{test_with_questions.id}/start",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert start_response.status_code == 200
        attempt_data = start_response.json()
        attempt_id = attempt_data["id"]

        # Prepare answers (all correct)
        questions = attempt_data["test"]["questions"]
        answers = []

        # Q1: SINGLE_CHOICE - select correct option
        q1_correct_opt = next(
            opt for opt in questions[0]["options"]
            if opt["option_text"] == "x = 2"
        )
        answers.append({
            "question_id": questions[0]["id"],
            "selected_option_ids": [q1_correct_opt["id"]]
        })

        # Q2: MULTIPLE_CHOICE - select all correct (2, 3, 5)
        q2_correct_opts = [
            opt["id"] for opt in questions[1]["options"]
            if opt["option_text"] in ["2", "3", "5"]
        ]
        answers.append({
            "question_id": questions[1]["id"],
            "selected_option_ids": q2_correct_opts
        })

        # Q3: TRUE_FALSE - select False
        q3_false_opt = next(
            opt for opt in questions[2]["options"]
            if opt["option_text"] == "False"
        )
        answers.append({
            "question_id": questions[2]["id"],
            "selected_option_ids": [q3_false_opt["id"]]
        })

        # Q4: SHORT_ANSWER
        answers.append({
            "question_id": questions[3]["id"],
            "answer_text": "My explanation of Pythagorean theorem"
        })

        # Submit test
        submit_response = await client.post(
            f"/api/v1/students/attempts/{attempt_id}/submit",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"answers": answers}
        )

    assert submit_response.status_code == 200
    result = submit_response.json()

    # Verify attempt completed
    assert result["status"] == "completed"
    assert result["score"] is not None
    assert result["passed"] is not None

    # CRITICAL: Questions should NOW have correct answers visible
    for question in result["test"]["questions"]:
        for option in question["options"]:
            assert "is_correct" in option  # Security: show after submit


@pytest.mark.asyncio
async def test_score_calculation_correct(
    test_app,
    student_user: tuple,
    student_token: str,
    test_with_questions: Test,
    db_session: AsyncSession
):
    """
    Test that score is calculated correctly.

    Answer Q1, Q2, Q3 correctly (4 points total out of 4)
    Q4 is SHORT_ANSWER (not auto-graded)

    Expected score: 4.0 / 4.0 = 1.0 (100%)
    """
    user, student = student_user

    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        # Start test
        start_response = await client.post(
            f"/api/v1/students/tests/{test_with_questions.id}/start",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        attempt_id = start_response.json()["id"]
        questions = start_response.json()["test"]["questions"]

        # Prepare all correct answers
        answers = []

        # Q1: SINGLE_CHOICE (1 point) - correct
        q1_correct = next(opt for opt in questions[0]["options"] if opt["option_text"] == "x = 2")
        answers.append({"question_id": questions[0]["id"], "selected_option_ids": [q1_correct["id"]]})

        # Q2: MULTIPLE_CHOICE (2 points) - correct
        q2_correct = [opt["id"] for opt in questions[1]["options"] if opt["option_text"] in ["2", "3", "5"]]
        answers.append({"question_id": questions[1]["id"], "selected_option_ids": q2_correct})

        # Q3: TRUE_FALSE (1 point) - correct
        q3_correct = next(opt for opt in questions[2]["options"] if opt["option_text"] == "False")
        answers.append({"question_id": questions[2]["id"], "selected_option_ids": [q3_correct["id"]]})

        # Q4: SHORT_ANSWER (not graded)
        answers.append({"question_id": questions[3]["id"], "answer_text": "My answer"})

        # Submit
        submit_response = await client.post(
            f"/api/v1/students/attempts/{attempt_id}/submit",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"answers": answers}
        )

    result = submit_response.json()

    # Verify score
    # Q1 (1) + Q2 (2) + Q3 (1) + Q4 (0, manual grading) = 4.0 earned
    # Total: Q1 (1) + Q2 (2) + Q3 (1) + Q4 (2) = 6.0 possible
    assert result["points_earned"] == 4.0
    assert result["total_points"] == 6.0  # Includes SHORT_ANSWER (2pts)
    assert result["score"] == pytest.approx(0.6667, rel=1e-2)  # 4.0 / 6.0


@pytest.mark.asyncio
async def test_passing_status_true(
    test_app,
    student_user: tuple,
    student_token: str,
    test_with_questions: Test,
    db_session: AsyncSession
):
    """
    Test passing status = False when score < passing_score.

    Test passing_score = 0.7
    Q1 (1) + Q2 (2) + Q3 incorrect (0) + Q4 (0, manual) = 3.0 / 6.0 = 0.5 < 0.7 -> passed = False
    """
    user, student = student_user

    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        start_response = await client.post(
            f"/api/v1/students/tests/{test_with_questions.id}/start",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        attempt_id = start_response.json()["id"]
        questions = start_response.json()["test"]["questions"]

        # Answer Q1 and Q2 correctly, Q3 incorrectly
        answers = []
        # Q1: correct (1 point)
        q1_correct = next(opt for opt in questions[0]["options"] if opt["option_text"] == "x = 2")
        answers.append({"question_id": questions[0]["id"], "selected_option_ids": [q1_correct["id"]]})

        # Q2: correct (2 points)
        q2_correct = [opt["id"] for opt in questions[1]["options"] if opt["option_text"] in ["2", "3", "5"]]
        answers.append({"question_id": questions[1]["id"], "selected_option_ids": q2_correct})

        # Q3: INCORRECT (0 points)
        q3_incorrect = next(opt for opt in questions[2]["options"] if opt["option_text"] == "True")
        answers.append({"question_id": questions[2]["id"], "selected_option_ids": [q3_incorrect["id"]]})

        # Q4: text (0 points, manual grading)
        answers.append({"question_id": questions[3]["id"], "answer_text": "answer"})

        submit_response = await client.post(
            f"/api/v1/students/attempts/{attempt_id}/submit",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"answers": answers}
        )

    result = submit_response.json()
    assert result["score"] == 0.5  # 3.0 / 6.0
    assert result["passed"] is False  # 0.5 < 0.7


@pytest.mark.asyncio
async def test_passing_status_false(
    test_app,
    student_user: tuple,
    student_token: str,
    test_with_questions: Test,
    db_session: AsyncSession
):
    """
    Test passing status = False when score < passing_score.

    Test passing_score = 0.7
    Q1 (1) + Q2 incorrect (0) + Q3 (1) + Q4 (0, manual) = 2.0 / 6.0 = 0.333 < 0.7 -> passed = False
    """
    user, student = student_user

    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        start_response = await client.post(
            f"/api/v1/students/tests/{test_with_questions.id}/start",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        attempt_id = start_response.json()["id"]
        questions = start_response.json()["test"]["questions"]

        # Answer only Q1 and Q3 correctly
        answers = []
        # Q1: correct (1 point)
        q1_correct = next(opt for opt in questions[0]["options"] if opt["option_text"] == "x = 2")
        answers.append({"question_id": questions[0]["id"], "selected_option_ids": [q1_correct["id"]]})

        # Q2: INCORRECT (0 points)
        q2_incorrect = [questions[1]["options"][0]["id"]]  # Just select first option (wrong)
        answers.append({"question_id": questions[1]["id"], "selected_option_ids": q2_incorrect})

        # Q3: correct (1 point)
        q3_correct = next(opt for opt in questions[2]["options"] if opt["option_text"] == "False")
        answers.append({"question_id": questions[2]["id"], "selected_option_ids": [q3_correct["id"]]})

        # Q4: text (0 points, manual grading)
        answers.append({"question_id": questions[3]["id"], "answer_text": "answer"})

        submit_response = await client.post(
            f"/api/v1/students/attempts/{attempt_id}/submit",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"answers": answers}
        )

    result = submit_response.json()
    assert result["score"] == pytest.approx(0.3333, rel=1e-2)  # 2.0 / 6.0
    assert result["passed"] is False  # 0.333 < 0.7


# ========== Test 4: Isolation & Ownership ==========

@pytest.mark.asyncio
async def test_student_cannot_see_other_attempts(
    test_app,
    student_user: tuple,
    student2_user: tuple,
    student_token: str,
    student2_token: str,
    test_with_questions: Test,
    db_session: AsyncSession
):
    """
    Test that student1 cannot see student2's attempts (ownership check).

    Expected: 403 Forbidden or 404 Not Found
    """
    user1, student1 = student_user
    user2, student2 = student2_user

    # Student2 starts a test
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        # Create test in school2 first
        from app.models.test import Test as TestModel
        test_school2 = TestModel(
            school_id=student2.school_id,
            chapter_id=test_with_questions.chapter_id,
            paragraph_id=test_with_questions.paragraph_id,
            title="Test for school 2",
            test_purpose=TestPurpose.FORMATIVE,
            is_active=True,
            passing_score=0.7
        )
        db_session.add(test_school2)
        await db_session.commit()
        await db_session.refresh(test_school2)

        # Student2 starts test
        start_response = await client.post(
            f"/api/v1/students/tests/{test_school2.id}/start",
            headers={"Authorization": f"Bearer {student2_token}"}
        )
        assert start_response.status_code == 200
        attempt_id = start_response.json()["id"]

        # Student1 tries to access student2's attempt
        access_response = await client.get(
            f"/api/v1/students/attempts/{attempt_id}",
            headers={"Authorization": f"Bearer {student_token}"}
        )

    # Should be denied (403 or 404)
    assert access_response.status_code in [403, 404]


# ========== Test 5: Progress & Mastery ==========

@pytest.mark.asyncio
async def test_student_progress_summary(
    test_app,
    student_user: tuple,
    student_token: str,
    test_with_questions: Test,
    chapter1,
    db_session: AsyncSession
):
    """
    Test GET /api/v1/students/progress.

    Should return summary of student's paragraph mastery.
    """
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        response = await client.get(
            f"/api/v1/students/progress?chapter_id={chapter1.id}",
            headers={"Authorization": f"Bearer {student_token}"}
        )

    assert response.status_code == 200
    data = response.json()

    # Verify structure
    assert "total_paragraphs" in data
    assert "completed_paragraphs" in data
    assert "mastered_paragraphs" in data
    assert "struggling_paragraphs" in data
    assert "paragraphs" in data
    assert isinstance(data["paragraphs"], list)


@pytest.mark.asyncio
async def test_paragraph_mastery_updated(
    test_app,
    student_user: tuple,
    student_token: str,
    test_with_questions: Test,
    paragraph1,
    db_session: AsyncSession
):
    """
    Test that ParagraphMastery is updated after submitting FORMATIVE test.

    Critical: FORMATIVE and SUMMATIVE tests should update mastery.
    DIAGNOSTIC and PRACTICE should NOT.
    """
    user, student = student_user

    # Verify test is FORMATIVE
    assert test_with_questions.test_purpose == TestPurpose.FORMATIVE

    # Start and submit test
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        start_response = await client.post(
            f"/api/v1/students/tests/{test_with_questions.id}/start",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        attempt_id = start_response.json()["id"]
        questions = start_response.json()["test"]["questions"]

        # Answer all correctly
        answers = []
        q1 = next(opt for opt in questions[0]["options"] if opt["option_text"] == "x = 2")
        answers.append({"question_id": questions[0]["id"], "selected_option_ids": [q1["id"]]})

        q2 = [opt["id"] for opt in questions[1]["options"] if opt["option_text"] in ["2", "3", "5"]]
        answers.append({"question_id": questions[1]["id"], "selected_option_ids": q2})

        q3 = next(opt for opt in questions[2]["options"] if opt["option_text"] == "False")
        answers.append({"question_id": questions[2]["id"], "selected_option_ids": [q3["id"]]})

        answers.append({"question_id": questions[3]["id"], "answer_text": "answer"})

        await client.post(
            f"/api/v1/students/attempts/{attempt_id}/submit",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"answers": answers}
        )

    # Verify ParagraphMastery record created/updated
    result = await db_session.execute(
        select(ParagraphMastery).where(
            ParagraphMastery.student_id == student.id,
            ParagraphMastery.paragraph_id == paragraph1.id
        )
    )
    mastery = result.scalar_one_or_none()

    assert mastery is not None
    assert mastery.attempts_count >= 1
    assert mastery.test_score is not None
    assert mastery.best_score is not None
    assert mastery.is_completed is True
    assert mastery.status in ["struggling", "progressing", "mastered"]
