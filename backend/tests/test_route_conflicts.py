"""
Tests for API route ordering / conflicts.

Bug: GET /teachers/quiz-sessions/tournaments matched /{session_id}
with session_id="tournaments" → 422 (can't parse string as int).

Fix: Moved /tournaments route before /{session_id} in the router.

These tests ensure that static routes are not shadowed by dynamic
path parameters.
"""
import pytest
from httpx import ASGITransport, AsyncClient


class TestTeacherQuizRouteOrdering:
    """Verify /tournaments is not captured by /{session_id}."""

    @pytest.mark.asyncio
    async def test_tournaments_returns_200_not_422(self, test_app, teacher_token):
        """
        REGRESSION: GET /teachers/quiz-sessions/tournaments must NOT
        return 422 (which would mean it matched /{session_id}).
        """
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/teachers/quiz-sessions/tournaments",
                headers={"Authorization": f"Bearer {teacher_token}"},
            )

        # 200 with empty list, or 200 with data — but NOT 422
        assert response.status_code != 422, (
            "Route conflict: /tournaments matched /{session_id}"
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_session_by_numeric_id_still_works(self, test_app, teacher_token):
        """/{session_id} with numeric ID should work (404 if not found)."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/teachers/quiz-sessions/99999",
                headers={"Authorization": f"Bearer {teacher_token}"},
            )

        # 404 (session not found), not 422
        assert response.status_code in (404, 400)

    @pytest.mark.asyncio
    async def test_tournament_results_not_captured_by_session_id(
        self, test_app, teacher_token
    ):
        """GET /tournaments/{id}/results should not hit /{session_id}."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/teachers/quiz-sessions/tournaments/999/results",
                headers={"Authorization": f"Bearer {teacher_token}"},
            )

        assert response.status_code != 422
        assert response.status_code == 404  # Tournament not found

    @pytest.mark.asyncio
    async def test_tournaments_requires_auth(self, test_app):
        """No auth on tournaments → 401/403, not 422."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/teachers/quiz-sessions/tournaments",
            )

        assert response.status_code in (401, 403)


class TestStudentQuizRouteOrdering:
    """Verify student quiz routes don't conflict."""

    @pytest.mark.asyncio
    async def test_my_quizzes_returns_200(self, test_app, student_token):
        """GET /students/quiz-sessions/my-quizzes should not hit /{session_id}."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/students/quiz-sessions/my-quizzes",
                headers={"Authorization": f"Bearer {student_token}"},
            )

        assert response.status_code != 422
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_join_quiz_requires_student_role(self, test_app, teacher_token):
        """Teacher cannot join quiz → 403."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/students/quiz-sessions/join",
                headers={"Authorization": f"Bearer {teacher_token}"},
                json={"join_code": "000000"},
            )

        assert response.status_code == 403
