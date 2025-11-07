"""
Tests for Users, Students, Teachers, Parents, and Classes API endpoints.
Critical tests to verify data isolation and CRUD operations for Iteration 5D.
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date

from app.main import app
from app.models.user import User, UserRole
from app.models.school import School
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.parent import Parent
from app.models.school_class import SchoolClass
from app.core.security import get_password_hash, create_access_token
from app.core.database import get_db


# ========== Fixtures ==========

@pytest_asyncio.fixture
async def test_app(db_session: AsyncSession):
    """
    Override app's get_db dependency to use test database session.
    """
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield app
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def school1(db_session: AsyncSession) -> School:
    """Create first test school."""
    school = School(
        name="School 1",
        code="school-1",
        email="school1@test.com",
        is_active=True,
    )
    db_session.add(school)
    await db_session.commit()
    await db_session.refresh(school)
    return school


@pytest_asyncio.fixture
async def school2(db_session: AsyncSession) -> School:
    """Create second test school for isolation tests."""
    school = School(
        name="School 2",
        code="school-2",
        email="school2@test.com",
        is_active=True,
    )
    db_session.add(school)
    await db_session.commit()
    await db_session.refresh(school)
    return school


@pytest_asyncio.fixture
async def admin1(db_session: AsyncSession, school1: School) -> User:
    """Create admin user for school 1."""
    user = User(
        email="admin1@test.com",
        password_hash=get_password_hash("password123"),
        first_name="Admin",
        last_name="One",
        role=UserRole.ADMIN,
        school_id=school1.id,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin2(db_session: AsyncSession, school2: School) -> User:
    """Create admin user for school 2."""
    user = User(
        email="admin2@test.com",
        password_hash=get_password_hash("password123"),
        first_name="Admin",
        last_name="Two",
        role=UserRole.ADMIN,
        school_id=school2.id,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin1_token(admin1: User) -> str:
    """Create access token for admin1."""
    return create_access_token(data={"sub": str(admin1.id)})


@pytest_asyncio.fixture
async def admin2_token(admin2: User) -> str:
    """Create access token for admin2."""
    return create_access_token(data={"sub": str(admin2.id)})


@pytest_asyncio.fixture
async def student1(db_session: AsyncSession, school1: School) -> Student:
    """Create a test student in school1."""
    # Create user first
    user = User(
        email="student1@test.com",
        password_hash=get_password_hash("password123"),
        first_name="Student",
        last_name="One",
        role=UserRole.STUDENT,
        school_id=school1.id,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    # Create student
    student = Student(
        school_id=school1.id,
        user_id=user.id,
        student_code="STU0720240001",
        grade_level=7,
        birth_date=date(2010, 1, 1),
    )
    db_session.add(student)
    await db_session.commit()
    await db_session.refresh(student)
    return student


@pytest_asyncio.fixture
async def class1(db_session: AsyncSession, school1: School) -> SchoolClass:
    """Create a test class in school1."""
    school_class = SchoolClass(
        school_id=school1.id,
        name="7A",
        code="7A-2024",
        grade_level=7,
        academic_year="2024-2025",
    )
    db_session.add(school_class)
    await db_session.commit()
    await db_session.refresh(school_class)
    return school_class


# ========== Tests ==========

@pytest.mark.asyncio
async def test_fixture_creates_admin_correctly(
    db_session: AsyncSession,
    test_app,
    admin1: User,
    school1: School,
):
    """
    Sanity check: Verify that admin1 fixture creates user with correct role.
    """
    assert admin1 is not None
    assert admin1.role == UserRole.ADMIN, f"Expected ADMIN role, got {admin1.role}"
    assert admin1.school_id == school1.id
    assert admin1.is_active is True


@pytest.mark.asyncio
async def test_admin_creates_student(
    db_session: AsyncSession,
    test_app,
    admin1: User,
    admin1_token: str,
    school1: School,
):
    """
    Test that ADMIN can create a student (transactional User + Student creation).
    Tests the critical transactional pattern for creating users.
    """
    student_data = {
        "email": "newstudent@test.com",
        "password": "password123",
        "first_name": "New",
        "last_name": "Student",
        "middle_name": "Test",
        "phone": "+1234567890",
        "grade_level": 8,
        "birth_date": "2009-05-15",
        "student_code": None,  # Should be auto-generated
    }

    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/admin/school/students",
            json=student_data,
            headers={"Authorization": f"Bearer {admin1_token}"},
        )

        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        student = response.json()

        # Verify student data
        assert student["grade_level"] == 8
        assert student["school_id"] == school1.id
        assert student["student_code"] is not None  # Auto-generated
        assert student["student_code"].startswith("STU")

        # Verify user data (nested)
        assert student["user"]["email"] == "newstudent@test.com"
        assert student["user"]["first_name"] == "New"
        assert student["user"]["last_name"] == "Student"
        assert student["user"]["role"] == "student"  # lowercase enum value
        assert student["user"]["is_active"] is True


@pytest.mark.asyncio
async def test_admin_cannot_see_other_school_students(
    db_session: AsyncSession,
    test_app,
    admin1_token: str,
    admin2_token: str,
    school1: School,
    school2: School,
):
    """
    Test data isolation: Admin of school1 cannot see students from school2.
    This is a CRITICAL test for multi-tenancy.
    """
    # Create student in school1
    student1_data = {
        "email": "school1student@test.com",
        "password": "password123",
        "first_name": "School1",
        "last_name": "Student",
        "grade_level": 7,
    }

    # Create student in school2
    student2_data = {
        "email": "school2student@test.com",
        "password": "password123",
        "first_name": "School2",
        "last_name": "Student",
        "grade_level": 7,
    }

    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as client:
        # Admin1 creates student in school1
        response1 = await client.post(
            "/api/v1/admin/school/students",
            json=student1_data,
            headers={"Authorization": f"Bearer {admin1_token}"},
        )
        assert response1.status_code == 201
        student1 = response1.json()

        # Admin2 creates student in school2
        response2 = await client.post(
            "/api/v1/admin/school/students",
            json=student2_data,
            headers={"Authorization": f"Bearer {admin2_token}"},
        )
        assert response2.status_code == 201
        student2 = response2.json()

        # Admin1 lists students - should only see school1 student
        response = await client.get(
            "/api/v1/admin/school/students",
            headers={"Authorization": f"Bearer {admin1_token}"},
        )
        assert response.status_code == 200
        students = response.json()

        student_ids = [s["id"] for s in students]
        assert student1["id"] in student_ids
        assert student2["id"] not in student_ids  # ISOLATION: should NOT see school2 student

        # Admin1 tries to access school2 student directly - should get 404 (not found) or 403 (access denied)
        response = await client.get(
            f"/api/v1/admin/school/students/{student2['id']}",
            headers={"Authorization": f"Bearer {admin1_token}"},
        )
        assert response.status_code in [403, 404]  # Access denied or not found


@pytest.mark.asyncio
async def test_student_code_autogeneration(
    db_session: AsyncSession,
    test_app,
    admin1_token: str,
    school1: School,
):
    """
    Test that student_code is auto-generated in format STU{grade}{year}{sequence}.
    """
    student_data = {
        "email": "autogen@test.com",
        "password": "password123",
        "first_name": "Auto",
        "last_name": "Generated",
        "grade_level": 9,
        "birth_date": "2008-03-20",
    }

    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/admin/school/students",
            json=student_data,
            headers={"Authorization": f"Bearer {admin1_token}"},
        )

        assert response.status_code == 201
        student = response.json()

        # Verify auto-generated code format
        assert student["student_code"] is not None
        assert student["student_code"].startswith("STU9")  # Grade 9 (may be 1 or 2 digits)
        assert len(student["student_code"]) >= 8  # STU + grade(1-2) + year(4) + seq


@pytest.mark.asyncio
async def test_admin_adds_students_to_class(
    db_session: AsyncSession,
    test_app,
    admin1_token: str,
    school1: School,
    class1: SchoolClass,
):
    """
    Test bulk adding students to a class.
    Tests the Transfer List functionality.
    """
    # Create 2 students first
    student_ids = []
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as client:
        for i in range(2):
            student_data = {
                "email": f"bulkstudent{i}@test.com",
                "password": "password123",
                "first_name": f"Student{i}",
                "last_name": "Bulk",
                "grade_level": 7,
            }
            response = await client.post(
                "/api/v1/admin/school/students",
                json=student_data,
                headers={"Authorization": f"Bearer {admin1_token}"},
            )
            assert response.status_code == 201
            student_ids.append(response.json()["id"])

        # Bulk add students to class
        add_request = {"student_ids": student_ids}
        response = await client.post(
            f"/api/v1/admin/school/classes/{class1.id}/students",
            json=add_request,
            headers={"Authorization": f"Bearer {admin1_token}"},
        )

        assert response.status_code == 200
        result = response.json()

        # Verify students were added
        added_ids = [s["id"] for s in result.get("students", [])]
        assert student_ids[0] in added_ids
        assert student_ids[1] in added_ids


@pytest.mark.asyncio
async def test_soft_delete_cascades(
    db_session: AsyncSession,
    test_app,
    admin1_token: str,
    student1: Student,
):
    """
    Test that soft deleting a student sets deleted_at and is_deleted.
    """
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as client:
        # Delete student
        response = await client.delete(
            f"/api/v1/admin/school/students/{student1.id}",
            headers={"Authorization": f"Bearer {admin1_token}"},
        )
        assert response.status_code == 204

        # Trying to get deleted student should return 404
        response = await client.get(
            f"/api/v1/admin/school/students/{student1.id}",
            headers={"Authorization": f"Bearer {admin1_token}"},
        )
        assert response.status_code == 404

        # Student should not appear in list
        response = await client.get(
            "/api/v1/admin/school/students",
            headers={"Authorization": f"Bearer {admin1_token}"},
        )
        assert response.status_code == 200
        students = response.json()
        student_ids = [s["id"] for s in students]
        assert student1.id not in student_ids


@pytest.mark.asyncio
async def test_parent_children_management(
    db_session: AsyncSession,
    test_app,
    admin1_token: str,
    school1: School,
    student1: Student,
):
    """
    Test parent-children relationship management.
    """
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as client:
        # Create parent with initial child
        parent_data = {
            "email": "parent@test.com",
            "password": "password123",
            "first_name": "Parent",
            "last_name": "Test",
            "phone": "+1234567890",
            "student_ids": [student1.id],  # Initial children
        }

        response = await client.post(
            "/api/v1/admin/school/parents",
            json=parent_data,
            headers={"Authorization": f"Bearer {admin1_token}"},
        )

        assert response.status_code == 201
        parent = response.json()
        assert parent["user"]["email"] == "parent@test.com"

        parent_id = parent["id"]

        # Get children
        response = await client.get(
            f"/api/v1/admin/school/parents/{parent_id}/children",
            headers={"Authorization": f"Bearer {admin1_token}"},
        )
        assert response.status_code == 200
        children = response.json()
        assert len(children) == 1
        assert children[0]["id"] == student1.id

        # Create another student to add
        student2_data = {
            "email": "student2@test.com",
            "password": "password123",
            "first_name": "Student",
            "last_name": "Two",
            "grade_level": 8,
        }
        response = await client.post(
            "/api/v1/admin/school/students",
            json=student2_data,
            headers={"Authorization": f"Bearer {admin1_token}"},
        )
        assert response.status_code == 201
        student2 = response.json()

        # Add second child
        response = await client.post(
            f"/api/v1/admin/school/parents/{parent_id}/children",
            json={"student_ids": [student2["id"]]},
            headers={"Authorization": f"Bearer {admin1_token}"},
        )
        assert response.status_code == 200

        # Verify now has 2 children
        response = await client.get(
            f"/api/v1/admin/school/parents/{parent_id}/children",
            headers={"Authorization": f"Bearer {admin1_token}"},
        )
        assert response.status_code == 200
        children = response.json()
        assert len(children) == 2

        # Remove first child
        response = await client.delete(
            f"/api/v1/admin/school/parents/{parent_id}/children/{student1.id}",
            headers={"Authorization": f"Bearer {admin1_token}"},
        )
        assert response.status_code in [200, 204]  # Either 200 OK or 204 No Content

        # Verify now has 1 child
        response = await client.get(
            f"/api/v1/admin/school/parents/{parent_id}/children",
            headers={"Authorization": f"Bearer {admin1_token}"},
        )
        assert response.status_code == 200
        children = response.json()
        assert len(children) == 1
        assert children[0]["id"] == student2["id"]


@pytest.mark.asyncio
async def test_class_students_unique_constraint(
    db_session: AsyncSession,
    test_app,
    admin1_token: str,
    class1: SchoolClass,
    student1: Student,
):
    """
    Test that adding the same student to a class twice fails (unique constraint).
    """
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as client:
        # Add student to class first time
        response = await client.post(
            f"/api/v1/admin/school/classes/{class1.id}/students",
            json={"student_ids": [student1.id]},
            headers={"Authorization": f"Bearer {admin1_token}"},
        )
        assert response.status_code == 200

        # Try to add same student again - should handle gracefully
        response = await client.post(
            f"/api/v1/admin/school/classes/{class1.id}/students",
            json={"student_ids": [student1.id]},
            headers={"Authorization": f"Bearer {admin1_token}"},
        )
        # Should either return 200 (idempotent) or 400 (already exists)
        assert response.status_code in [200, 400]


@pytest.mark.asyncio
async def test_deactivate_user(
    db_session: AsyncSession,
    test_app,
    admin1_token: str,
    student1: Student,
):
    """
    Test deactivating and activating a user.
    """
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as client:
        # Get user_id from student
        response = await client.get(
            f"/api/v1/admin/school/students/{student1.id}",
            headers={"Authorization": f"Bearer {admin1_token}"},
        )
        assert response.status_code == 200
        student_data = response.json()
        user_id = student_data["user"]["id"]

        # Deactivate user
        response = await client.post(
            f"/api/v1/admin/school/users/{user_id}/deactivate",
            headers={"Authorization": f"Bearer {admin1_token}"},
        )
        assert response.status_code == 200
        user = response.json()
        assert user["is_active"] is False

        # Activate user
        response = await client.post(
            f"/api/v1/admin/school/users/{user_id}/activate",
            headers={"Authorization": f"Bearer {admin1_token}"},
        )
        assert response.status_code == 200
        user = response.json()
        assert user["is_active"] is True


@pytest.mark.asyncio
async def test_filters_work(
    db_session: AsyncSession,
    test_app,
    admin1_token: str,
    school1: School,
):
    """
    Test that filtering works correctly (grade_level, is_active).
    """
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as client:
        # Create students with different grade levels
        for grade in [7, 8, 9]:
            student_data = {
                "email": f"grade{grade}@test.com",
                "password": "password123",
                "first_name": f"Grade{grade}",
                "last_name": "Student",
                "grade_level": grade,
            }
            response = await client.post(
                "/api/v1/admin/school/students",
                json=student_data,
                headers={"Authorization": f"Bearer {admin1_token}"},
            )
            assert response.status_code == 201

        # Filter by grade_level=7
        response = await client.get(
            "/api/v1/admin/school/students?grade_level=7",
            headers={"Authorization": f"Bearer {admin1_token}"},
        )
        assert response.status_code == 200
        students = response.json()

        # Should only have grade 7 students
        for student in students:
            assert student["grade_level"] == 7

        # Filter by is_active=true
        response = await client.get(
            "/api/v1/admin/school/students?is_active=true",
            headers={"Authorization": f"Bearer {admin1_token}"},
        )
        assert response.status_code == 200
        students = response.json()

        # All returned students should be active
        for student in students:
            assert student["user"]["is_active"] is True


@pytest.mark.asyncio
async def test_teacher_creation_and_filtering(
    db_session: AsyncSession,
    test_app,
    admin1_token: str,
    school1: School,
):
    """
    Test creating teachers and filtering by subject.
    """
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as client:
        # Create math teacher
        teacher_data = {
            "email": "mathteacher@test.com",
            "password": "password123",
            "first_name": "Math",
            "last_name": "Teacher",
            "subject": "Mathematics",
            "bio": "Experienced math teacher",
        }

        response = await client.post(
            "/api/v1/admin/school/teachers",
            json=teacher_data,
            headers={"Authorization": f"Bearer {admin1_token}"},
        )

        assert response.status_code == 201
        teacher = response.json()
        assert teacher["subject"] == "Mathematics"
        assert teacher["teacher_code"] is not None  # Auto-generated
        assert teacher["teacher_code"].startswith("TCHR")
        assert teacher["user"]["email"] == "mathteacher@test.com"

        # Create physics teacher
        teacher_data2 = {
            "email": "physicsteacher@test.com",
            "password": "password123",
            "first_name": "Physics",
            "last_name": "Teacher",
            "subject": "Physics",
        }

        response = await client.post(
            "/api/v1/admin/school/teachers",
            json=teacher_data2,
            headers={"Authorization": f"Bearer {admin1_token}"},
        )
        assert response.status_code == 201

        # Filter by subject=Mathematics
        response = await client.get(
            "/api/v1/admin/school/teachers?subject=Mathematics",
            headers={"Authorization": f"Bearer {admin1_token}"},
        )
        assert response.status_code == 200
        teachers = response.json()

        # Should only have math teachers
        for teacher in teachers:
            assert teacher["subject"] == "Mathematics"


@pytest.mark.asyncio
async def test_class_code_uniqueness(
    db_session: AsyncSession,
    test_app,
    admin1_token: str,
    school1: School,
    class1: SchoolClass,
):
    """
    Test that class code must be unique within a school.
    """
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as client:
        # Try to create class with duplicate code
        class_data = {
            "name": "7B",
            "code": class1.code,  # Duplicate code
            "grade_level": 7,
            "academic_year": "2024-2025",
        }

        response = await client.post(
            "/api/v1/admin/school/classes",
            json=class_data,
            headers={"Authorization": f"Bearer {admin1_token}"},
        )

        # Should fail with 409 Conflict
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"].lower()
