"""
Tests for Lab API — interactive laboratory endpoints.

Covers:
- GET /students/lab/available
- GET /students/lab/{id}
- GET /students/lab/{id}/progress
- POST /students/lab/{id}/progress
- GET /students/lab/{id}/tasks
- POST /students/lab/{id}/tasks/{task_id}/answer
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subject import Subject
from app.models.lab import Lab, LabTask
from app.models.student import Student
from app.models.user import User


# ========== Fixtures ==========

@pytest_asyncio.fixture
async def subject_history(db_session: AsyncSession) -> Subject:
    """Create a history subject."""
    subject = Subject(
        code="history_kz_test",
        name_ru="История Казахстана",
        name_kz="Қазақстан тарихы",
    )
    db_session.add(subject)
    await db_session.commit()
    await db_session.refresh(subject)
    return subject


@pytest_asyncio.fixture
async def lab_history(db_session: AsyncSession, subject_history: Subject) -> Lab:
    """Create a history map lab (global, no school_id)."""
    lab = Lab(
        subject_id=subject_history.id,
        title="Қазақстан тарихы — интерактивті карта",
        description="Дәуірлер бойынша карта",
        lab_type="map",
        config={"center": [48.0, 66.9], "zoom": 5},
        is_active=True,
        school_id=None,
    )
    db_session.add(lab)
    await db_session.commit()
    await db_session.refresh(lab)
    return lab


@pytest_asyncio.fixture
async def lab_inactive(db_session: AsyncSession, subject_history: Subject) -> Lab:
    """Create an inactive lab."""
    lab = Lab(
        subject_id=subject_history.id,
        title="Inactive Lab",
        lab_type="map",
        is_active=False,
        school_id=None,
    )
    db_session.add(lab)
    await db_session.commit()
    await db_session.refresh(lab)
    return lab


@pytest_asyncio.fixture
async def lab_tasks(db_session: AsyncSession, lab_history: Lab) -> list[LabTask]:
    """Create test tasks for the history lab."""
    task_quiz = LabTask(
        lab_id=lab_history.id,
        title="Казахское ханство",
        task_type="quiz",
        task_data={
            "question": "Кто основал Казахское ханство?",
            "options": ["Керей и Жанибек", "Абылай", "Тауке"],
            "correct_answer": "Керей и Жанибек",
            "explanation": "Керей и Жанибек основали Казахское ханство в 1465 году",
        },
        xp_reward=15,
        order_index=0,
    )
    task_find = LabTask(
        lab_id=lab_history.id,
        title="Найди столицу",
        task_type="find_on_map",
        task_data={
            "question": "Покажи на карте Туркестан",
            "correct_answer": {"lat": 43.3, "lng": 68.25},
            "tolerance": 1.0,
        },
        xp_reward=10,
        order_index=1,
    )
    task_epoch = LabTask(
        lab_id=lab_history.id,
        title="Выбери эпоху",
        task_type="choose_epoch",
        task_data={
            "question": "К какой эпохе относится Золотая Орда?",
            "correct_answer": "golden_horde",
        },
        xp_reward=10,
        order_index=2,
    )
    db_session.add_all([task_quiz, task_find, task_epoch])
    await db_session.commit()
    for t in [task_quiz, task_find, task_epoch]:
        await db_session.refresh(t)
    return [task_quiz, task_find, task_epoch]


# ========== Tests ==========

class TestLabAvailable:
    """GET /students/lab/available"""

    @pytest.mark.asyncio
    async def test_list_available_labs(self, test_app, student_token, lab_history):
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/students/lab/available",
                headers={"Authorization": f"Bearer {student_token}"},
            )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["title"] == "Қазақстан тарихы — интерактивті карта"
        assert data[0]["lab_type"] == "map"

    @pytest.mark.asyncio
    async def test_inactive_labs_not_shown(self, test_app, student_token, lab_history, lab_inactive):
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/students/lab/available",
                headers={"Authorization": f"Bearer {student_token}"},
            )
        assert response.status_code == 200
        data = response.json()
        titles = [lab["title"] for lab in data]
        assert "Inactive Lab" not in titles

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(self, test_app):
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/students/lab/available")
        assert response.status_code in (401, 403)


class TestLabDetail:
    """GET /students/lab/{lab_id}"""

    @pytest.mark.asyncio
    async def test_get_lab_detail(self, test_app, student_token, lab_history):
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get(
                f"/api/v1/students/lab/{lab_history.id}",
                headers={"Authorization": f"Bearer {student_token}"},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == lab_history.id
        assert data["lab_type"] == "map"
        assert data["config"]["zoom"] == 5

    @pytest.mark.asyncio
    async def test_lab_not_found_returns_404(self, test_app, student_token):
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/students/lab/99999",
                headers={"Authorization": f"Bearer {student_token}"},
            )
        assert response.status_code == 404


class TestLabProgress:
    """GET/POST /students/lab/{lab_id}/progress"""

    @pytest.mark.asyncio
    async def test_progress_initially_null(self, test_app, student_token, lab_history):
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get(
                f"/api/v1/students/lab/{lab_history.id}/progress",
                headers={"Authorization": f"Bearer {student_token}"},
            )
        assert response.status_code == 200
        assert response.json() is None

    @pytest.mark.asyncio
    async def test_update_progress(self, test_app, student_token, lab_history):
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.post(
                f"/api/v1/students/lab/{lab_history.id}/progress",
                headers={"Authorization": f"Bearer {student_token}"},
                json={"progress_data": {"explored_epochs": ["saka", "turkic"]}},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["lab_id"] == lab_history.id
        assert data["progress_data"]["explored_epochs"] == ["saka", "turkic"]
        assert data["xp_earned"] == 0

    @pytest.mark.asyncio
    async def test_progress_upsert(self, test_app, student_token, lab_history):
        """Second update overwrites progress_data."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            # First update
            await client.post(
                f"/api/v1/students/lab/{lab_history.id}/progress",
                headers={"Authorization": f"Bearer {student_token}"},
                json={"progress_data": {"explored_epochs": ["saka"]}},
            )
            # Second update
            response = await client.post(
                f"/api/v1/students/lab/{lab_history.id}/progress",
                headers={"Authorization": f"Bearer {student_token}"},
                json={"progress_data": {"explored_epochs": ["saka", "turkic", "golden_horde"]}},
            )
        assert response.status_code == 200
        data = response.json()
        assert len(data["progress_data"]["explored_epochs"]) == 3


class TestLabTasks:
    """GET /students/lab/{lab_id}/tasks"""

    @pytest.mark.asyncio
    async def test_list_tasks(self, test_app, student_token, lab_history, lab_tasks):
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get(
                f"/api/v1/students/lab/{lab_history.id}/tasks",
                headers={"Authorization": f"Bearer {student_token}"},
            )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert data[0]["task_type"] == "quiz"
        assert data[1]["task_type"] == "find_on_map"
        assert data[2]["task_type"] == "choose_epoch"

    @pytest.mark.asyncio
    async def test_tasks_ordered_by_index(self, test_app, student_token, lab_history, lab_tasks):
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get(
                f"/api/v1/students/lab/{lab_history.id}/tasks",
                headers={"Authorization": f"Bearer {student_token}"},
            )
        data = response.json()
        orders = [t["order_index"] for t in data]
        assert orders == sorted(orders)


class TestLabTaskAnswer:
    """POST /students/lab/{lab_id}/tasks/{task_id}/answer"""

    @pytest.mark.asyncio
    async def test_correct_quiz_answer(self, test_app, student_token, lab_history, lab_tasks):
        task_quiz = lab_tasks[0]
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.post(
                f"/api/v1/students/lab/{lab_history.id}/tasks/{task_quiz.id}/answer",
                headers={"Authorization": f"Bearer {student_token}"},
                json={"answer_data": {"selected": "Керей и Жанибек"}},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["is_correct"] is True
        assert data["xp_earned"] == 15

    @pytest.mark.asyncio
    async def test_incorrect_quiz_answer(self, test_app, student_token, lab_history, lab_tasks):
        task_quiz = lab_tasks[0]
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.post(
                f"/api/v1/students/lab/{lab_history.id}/tasks/{task_quiz.id}/answer",
                headers={"Authorization": f"Bearer {student_token}"},
                json={"answer_data": {"selected": "Абылай"}},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["is_correct"] is False
        assert data["xp_earned"] == 0

    @pytest.mark.asyncio
    async def test_find_on_map_correct(self, test_app, student_token, lab_history, lab_tasks):
        task_find = lab_tasks[1]
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.post(
                f"/api/v1/students/lab/{lab_history.id}/tasks/{task_find.id}/answer",
                headers={"Authorization": f"Bearer {student_token}"},
                json={"answer_data": {"coordinates": {"lat": 43.5, "lng": 68.3}}},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["is_correct"] is True
        assert data["xp_earned"] == 10

    @pytest.mark.asyncio
    async def test_find_on_map_too_far(self, test_app, student_token, lab_history, lab_tasks):
        task_find = lab_tasks[1]
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.post(
                f"/api/v1/students/lab/{lab_history.id}/tasks/{task_find.id}/answer",
                headers={"Authorization": f"Bearer {student_token}"},
                json={"answer_data": {"coordinates": {"lat": 51.0, "lng": 71.0}}},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["is_correct"] is False

    @pytest.mark.asyncio
    async def test_choose_epoch_correct(self, test_app, student_token, lab_history, lab_tasks):
        task_epoch = lab_tasks[2]
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.post(
                f"/api/v1/students/lab/{lab_history.id}/tasks/{task_epoch.id}/answer",
                headers={"Authorization": f"Bearer {student_token}"},
                json={"answer_data": {"epoch_id": "golden_horde"}},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["is_correct"] is True
        assert data["xp_earned"] == 10

    @pytest.mark.asyncio
    async def test_repeat_answer_no_xp(self, test_app, student_token, lab_history, lab_tasks):
        """Answering the same task twice should return 0 XP."""
        task_quiz = lab_tasks[0]
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            # First answer
            await client.post(
                f"/api/v1/students/lab/{lab_history.id}/tasks/{task_quiz.id}/answer",
                headers={"Authorization": f"Bearer {student_token}"},
                json={"answer_data": {"selected": "Керей и Жанибек"}},
            )
            # Second answer — idempotent, 0 XP
            response = await client.post(
                f"/api/v1/students/lab/{lab_history.id}/tasks/{task_quiz.id}/answer",
                headers={"Authorization": f"Bearer {student_token}"},
                json={"answer_data": {"selected": "Керей и Жанибек"}},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["is_correct"] is True
        assert data["xp_earned"] == 0  # No XP on repeat

    @pytest.mark.asyncio
    async def test_task_not_found_returns_404(self, test_app, student_token, lab_history):
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.post(
                f"/api/v1/students/lab/{lab_history.id}/tasks/99999/answer",
                headers={"Authorization": f"Bearer {student_token}"},
                json={"answer_data": {"selected": "test"}},
            )
        assert response.status_code == 404
