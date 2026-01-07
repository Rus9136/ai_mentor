"""
Tests for homework RLS (Row Level Security) isolation.
Verifies that homework data is properly isolated between schools.
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.school import School
from app.models.user import User, UserRole
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.school_class import SchoolClass
from app.models.homework import (
    Homework, HomeworkTask, HomeworkTaskQuestion,
    HomeworkStudent, StudentTaskSubmission, StudentTaskAnswer,
    AIGenerationLog, HomeworkStatus, HomeworkTaskType,
    HomeworkQuestionType, AIOperationType
)
from app.core.security import get_password_hash
from app.core.tenancy import set_current_tenant, set_super_admin_flag, reset_tenant


@pytest.fixture
async def two_schools_setup(db_session: AsyncSession):
    """Create two schools with users and homework for testing isolation."""
    # Create schools
    school1 = School(name="School 1", code="SCH1")
    school2 = School(name="School 2", code="SCH2")
    db_session.add_all([school1, school2])
    await db_session.flush()

    # Create classes
    class1 = SchoolClass(
        school_id=school1.id,
        name="7A",
        grade_level=7,
        academic_year="2025-2026"
    )
    class2 = SchoolClass(
        school_id=school2.id,
        name="8B",
        grade_level=8,
        academic_year="2025-2026"
    )
    db_session.add_all([class1, class2])
    await db_session.flush()

    # Create users for school 1
    user1 = User(
        email="teacher1@school1.com",
        hashed_password=get_password_hash("password"),
        first_name="Teacher",
        last_name="One",
        role=UserRole.TEACHER,
        school_id=school1.id,
        is_active=True,
        is_verified=True,
    )
    student_user1 = User(
        email="student1@school1.com",
        hashed_password=get_password_hash("password"),
        first_name="Student",
        last_name="One",
        role=UserRole.STUDENT,
        school_id=school1.id,
        is_active=True,
        is_verified=True,
    )
    db_session.add_all([user1, student_user1])
    await db_session.flush()

    teacher1 = Teacher(
        user_id=user1.id,
        school_id=school1.id,
        subject="Math"
    )
    student1 = Student(
        user_id=student_user1.id,
        school_id=school1.id,
        grade_level=7
    )
    db_session.add_all([teacher1, student1])
    await db_session.flush()

    # Create users for school 2
    user2 = User(
        email="teacher2@school2.com",
        hashed_password=get_password_hash("password"),
        first_name="Teacher",
        last_name="Two",
        role=UserRole.TEACHER,
        school_id=school2.id,
        is_active=True,
        is_verified=True,
    )
    student_user2 = User(
        email="student2@school2.com",
        hashed_password=get_password_hash("password"),
        first_name="Student",
        last_name="Two",
        role=UserRole.STUDENT,
        school_id=school2.id,
        is_active=True,
        is_verified=True,
    )
    db_session.add_all([user2, student_user2])
    await db_session.flush()

    teacher2 = Teacher(
        user_id=user2.id,
        school_id=school2.id,
        subject="Physics"
    )
    student2 = Student(
        user_id=student_user2.id,
        school_id=school2.id,
        grade_level=8
    )
    db_session.add_all([teacher2, student2])
    await db_session.flush()

    # Create homework for school 1
    homework1 = Homework(
        school_id=school1.id,
        class_id=class1.id,
        teacher_id=teacher1.id,
        title="Math Homework School 1",
        status=HomeworkStatus.PUBLISHED,
        due_date=datetime.utcnow() + timedelta(days=7)
    )
    db_session.add(homework1)
    await db_session.flush()

    task1 = HomeworkTask(
        homework_id=homework1.id,
        school_id=school1.id,
        task_type=HomeworkTaskType.QUIZ,
        sort_order=1
    )
    db_session.add(task1)
    await db_session.flush()

    question1 = HomeworkTaskQuestion(
        homework_task_id=task1.id,
        school_id=school1.id,
        question_type=HomeworkQuestionType.SINGLE_CHOICE,
        question_text="What is 2+2?",
        options=[{"id": "a", "text": "4", "is_correct": True}],
        points=1
    )
    db_session.add(question1)
    await db_session.flush()

    # Create homework for school 2
    homework2 = Homework(
        school_id=school2.id,
        class_id=class2.id,
        teacher_id=teacher2.id,
        title="Physics Homework School 2",
        status=HomeworkStatus.PUBLISHED,
        due_date=datetime.utcnow() + timedelta(days=7)
    )
    db_session.add(homework2)
    await db_session.flush()

    task2 = HomeworkTask(
        homework_id=homework2.id,
        school_id=school2.id,
        task_type=HomeworkTaskType.OPEN_QUESTION,
        sort_order=1
    )
    db_session.add(task2)
    await db_session.flush()

    question2 = HomeworkTaskQuestion(
        homework_task_id=task2.id,
        school_id=school2.id,
        question_type=HomeworkQuestionType.OPEN_ENDED,
        question_text="Explain Newton's First Law",
        points=5
    )
    db_session.add(question2)
    await db_session.flush()

    # Create student assignments
    hw_student1 = HomeworkStudent(
        homework_id=homework1.id,
        student_id=student1.id,
        school_id=school1.id
    )
    hw_student2 = HomeworkStudent(
        homework_id=homework2.id,
        student_id=student2.id,
        school_id=school2.id
    )
    db_session.add_all([hw_student1, hw_student2])
    await db_session.flush()

    # Create submissions
    submission1 = StudentTaskSubmission(
        homework_student_id=hw_student1.id,
        homework_task_id=task1.id,
        student_id=student1.id,
        school_id=school1.id
    )
    submission2 = StudentTaskSubmission(
        homework_student_id=hw_student2.id,
        homework_task_id=task2.id,
        student_id=student2.id,
        school_id=school2.id
    )
    db_session.add_all([submission1, submission2])
    await db_session.flush()

    # Create answers
    answer1 = StudentTaskAnswer(
        submission_id=submission1.id,
        question_id=question1.id,
        student_id=student1.id,
        school_id=school1.id,
        selected_option_ids=["a"]
    )
    answer2 = StudentTaskAnswer(
        submission_id=submission2.id,
        question_id=question2.id,
        student_id=student2.id,
        school_id=school2.id,
        answer_text="An object at rest stays at rest..."
    )
    db_session.add_all([answer1, answer2])
    await db_session.flush()

    # Create AI logs (one with school_id, one global)
    ai_log1 = AIGenerationLog(
        school_id=school1.id,
        teacher_id=teacher1.id,
        homework_id=homework1.id,
        operation_type=AIOperationType.QUESTION_GENERATION,
        success=True
    )
    ai_log_global = AIGenerationLog(
        school_id=None,  # Global log
        operation_type=AIOperationType.FEEDBACK_GENERATION,
        success=True
    )
    db_session.add_all([ai_log1, ai_log_global])

    await db_session.commit()

    return {
        "school1": school1,
        "school2": school2,
        "homework1": homework1,
        "homework2": homework2,
        "task1": task1,
        "task2": task2,
        "question1": question1,
        "question2": question2,
        "student1": student1,
        "student2": student2,
        "ai_log1": ai_log1,
        "ai_log_global": ai_log_global,
    }


@pytest.mark.asyncio
async def test_homework_isolation_between_schools(
    db_session: AsyncSession,
    two_schools_setup: dict
):
    """Test that homework from one school is NOT visible to another school."""
    school1 = two_schools_setup["school1"]
    school2 = two_schools_setup["school2"]

    # Set tenant to school 1
    await set_current_tenant(db_session, school1.id)
    await set_super_admin_flag(db_session, False)
    await db_session.commit()

    # Query all homework
    result = await db_session.execute(select(Homework))
    visible_homework = result.scalars().all()

    # Should only see school 1 homework
    assert len(visible_homework) == 1
    assert visible_homework[0].school_id == school1.id
    assert visible_homework[0].title == "Math Homework School 1"


@pytest.mark.asyncio
async def test_homework_tasks_isolation(
    db_session: AsyncSession,
    two_schools_setup: dict
):
    """Test that homework_tasks are isolated by school_id."""
    school1 = two_schools_setup["school1"]

    await set_current_tenant(db_session, school1.id)
    await set_super_admin_flag(db_session, False)
    await db_session.commit()

    result = await db_session.execute(select(HomeworkTask))
    visible_tasks = result.scalars().all()

    assert len(visible_tasks) == 1
    assert visible_tasks[0].school_id == school1.id


@pytest.mark.asyncio
async def test_homework_task_questions_isolation(
    db_session: AsyncSession,
    two_schools_setup: dict
):
    """Test that homework_task_questions are isolated by school_id."""
    school2 = two_schools_setup["school2"]

    await set_current_tenant(db_session, school2.id)
    await set_super_admin_flag(db_session, False)
    await db_session.commit()

    result = await db_session.execute(select(HomeworkTaskQuestion))
    visible_questions = result.scalars().all()

    assert len(visible_questions) == 1
    assert visible_questions[0].school_id == school2.id
    assert "Newton" in visible_questions[0].question_text


@pytest.mark.asyncio
async def test_student_task_answers_isolation(
    db_session: AsyncSession,
    two_schools_setup: dict
):
    """Test that student answers are isolated by school."""
    school1 = two_schools_setup["school1"]

    await set_current_tenant(db_session, school1.id)
    await set_super_admin_flag(db_session, False)
    await db_session.commit()

    result = await db_session.execute(select(StudentTaskAnswer))
    visible_answers = result.scalars().all()

    assert len(visible_answers) == 1
    assert visible_answers[0].school_id == school1.id


@pytest.mark.asyncio
async def test_super_admin_sees_all_homework(
    db_session: AsyncSession,
    two_schools_setup: dict
):
    """Test that SUPER_ADMIN can see homework from all schools."""
    await set_super_admin_flag(db_session, True)
    await reset_tenant(db_session)
    await db_session.commit()

    result = await db_session.execute(select(Homework))
    all_homework = result.scalars().all()

    # Should see both schools' homework
    assert len(all_homework) == 2
    school_ids = {h.school_id for h in all_homework}
    assert len(school_ids) == 2


@pytest.mark.asyncio
async def test_ai_generation_logs_null_school_visible(
    db_session: AsyncSession,
    two_schools_setup: dict
):
    """Test that AI logs with NULL school_id are visible to all schools."""
    school1 = two_schools_setup["school1"]

    await set_current_tenant(db_session, school1.id)
    await set_super_admin_flag(db_session, False)
    await db_session.commit()

    result = await db_session.execute(select(AIGenerationLog))
    visible_logs = result.scalars().all()

    # Should see: own school log + global log (school_id IS NULL)
    assert len(visible_logs) == 2
    school_ids = {log.school_id for log in visible_logs}
    assert school1.id in school_ids
    assert None in school_ids  # Global log


@pytest.mark.asyncio
async def test_question_school_id_matches_task(
    db_session: AsyncSession,
    two_schools_setup: dict
):
    """Verify that question school_id is correctly denormalized from task."""
    await set_super_admin_flag(db_session, True)
    await reset_tenant(db_session)
    await db_session.commit()

    # Check all questions have matching school_id with their task
    result = await db_session.execute(
        select(HomeworkTaskQuestion, HomeworkTask)
        .join(HomeworkTask, HomeworkTaskQuestion.homework_task_id == HomeworkTask.id)
    )
    rows = result.all()

    for question, task in rows:
        assert question.school_id == task.school_id, (
            f"Question {question.id} school_id={question.school_id} "
            f"doesn't match task {task.id} school_id={task.school_id}"
        )


@pytest.mark.asyncio
async def test_insert_respects_rls(
    db_session: AsyncSession,
    two_schools_setup: dict
):
    """Test that INSERT operations respect RLS (can only insert to own school)."""
    school1 = two_schools_setup["school1"]
    school2 = two_schools_setup["school2"]

    await set_current_tenant(db_session, school1.id)
    await set_super_admin_flag(db_session, False)
    await db_session.commit()

    # Try to create homework for school1 (should succeed via trigger/RLS)
    new_homework = Homework(
        school_id=school1.id,
        class_id=two_schools_setup["homework1"].class_id,
        teacher_id=two_schools_setup["homework1"].teacher_id,
        title="New Homework for School 1",
        status=HomeworkStatus.DRAFT,
        due_date=datetime.utcnow() + timedelta(days=14)
    )
    db_session.add(new_homework)
    await db_session.flush()

    assert new_homework.id is not None
    assert new_homework.school_id == school1.id
