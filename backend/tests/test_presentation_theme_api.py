"""
Tests for PATCH /teachers/presentations/{id}/theme — re-theme without LLM.

Covers:
- Successful theme update
- 403: teacher doesn't own the presentation
- 404: presentation not found
- 422: invalid theme name
- slides_data unchanged after theme update
- Other context_data fields preserved
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.presentation import Presentation
from app.models.teacher import Teacher
from app.models.user import User


# ========== Fixtures ==========


@pytest_asyncio.fixture
async def presentation1(
    db_session: AsyncSession,
    teacher_user: tuple[User, Teacher],
    school1,
    paragraph1,
) -> Presentation:
    """Create a presentation owned by teacher_user in school1."""
    _, teacher = teacher_user
    pres = Presentation(
        teacher_id=teacher.id,
        school_id=school1.id,
        paragraph_id=paragraph1.id,
        language="kk",
        slide_count=5,
        title="Test Presentation",
        slides_data={
            "title": "Test",
            "slides": [
                {"type": "title", "title": "Hello", "subtitle": "World"},
                {"type": "content", "title": "Topic", "body": "Some content"},
            ],
        },
        context_data={
            "paragraph_title": "§1",
            "chapter_title": "Chapter 1",
            "textbook_title": "Algebra 7",
            "subject": "Математика",
            "grade_level": 7,
            "textbook_id": 1,
            "theme": "warm",
            "language": "kk",
        },
    )
    db_session.add(pres)
    await db_session.commit()
    await db_session.refresh(pres)
    return pres


# ========== Tests ==========


@pytest.mark.asyncio
async def test_update_theme_success(
    test_app, teacher_token, presentation1,
):
    """PATCH /theme returns 200, updates theme in context_data."""
    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test",
    ) as client:
        resp = await client.patch(
            f"/api/v1/teachers/presentations/{presentation1.id}/theme",
            json={"theme": "lavender"},
            headers={"Authorization": f"Bearer {teacher_token}"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == presentation1.id
    assert data["context_data"]["theme"] == "lavender"
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_update_theme_preserves_other_context_fields(
    test_app, teacher_token, presentation1,
):
    """Theme update must not remove other fields from context_data."""
    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test",
    ) as client:
        resp = await client.patch(
            f"/api/v1/teachers/presentations/{presentation1.id}/theme",
            json={"theme": "ocean"},
            headers={"Authorization": f"Bearer {teacher_token}"},
        )

    assert resp.status_code == 200
    ctx = resp.json()["context_data"]
    assert ctx["theme"] == "ocean"
    # Original fields preserved
    assert ctx["subject"] == "Математика"
    assert ctx["grade_level"] == 7
    assert ctx["language"] == "kk"
    assert ctx["paragraph_title"] == "§1"


@pytest.mark.asyncio
async def test_update_theme_does_not_touch_slides_data(
    test_app, db_session, teacher_token, presentation1,
):
    """slides_data must remain identical after theme change."""
    original_slides = dict(presentation1.slides_data)

    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test",
    ) as client:
        resp = await client.patch(
            f"/api/v1/teachers/presentations/{presentation1.id}/theme",
            json={"theme": "midnight"},
            headers={"Authorization": f"Bearer {teacher_token}"},
        )

    assert resp.status_code == 200

    # Re-fetch from DB to verify slides_data intact
    await db_session.refresh(presentation1)
    assert presentation1.slides_data == original_slides


@pytest.mark.asyncio
async def test_update_theme_not_owner(
    test_app, teacher2_token, presentation1,
):
    """Teacher from another school cannot change theme — 404 (not found for them)."""
    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test",
    ) as client:
        resp = await client.patch(
            f"/api/v1/teachers/presentations/{presentation1.id}/theme",
            json={"theme": "coral"},
            headers={"Authorization": f"Bearer {teacher2_token}"},
        )

    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_theme_not_found(
    test_app, teacher_token,
):
    """Non-existent presentation returns 404."""
    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test",
    ) as client:
        resp = await client.patch(
            "/api/v1/teachers/presentations/99999/theme",
            json={"theme": "coral"},
            headers={"Authorization": f"Bearer {teacher_token}"},
        )

    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_theme_invalid_theme(
    test_app, teacher_token, presentation1,
):
    """Invalid theme name returns 422."""
    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test",
    ) as client:
        resp = await client.patch(
            f"/api/v1/teachers/presentations/{presentation1.id}/theme",
            json={"theme": "neon_rainbow"},
            headers={"Authorization": f"Bearer {teacher_token}"},
        )

    assert resp.status_code == 422
