"""
Скрипт для заполнения ПРОДАКШН базы данных тестовыми данными.

ВАЖНО: Этот скрипт предназначен для production сервера!
Запускается через: ./deploy-infra.sh seed

Создает:
- SUPER_ADMIN и School ADMIN пользователей
- Школу "Тестовая школа №1" (SCHOOL001)
- 6 глобальных учебников с главами и параграфами
- 3 глобальных теста с вопросами
- 5 учителей для школы
- 8 учеников для школы
- 4 класса с распределением учеников
"""
import asyncio
import os
from datetime import date, datetime
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select

from app.models.school import School
from app.models.user import User, UserRole
from app.models.textbook import Textbook
from app.models.chapter import Chapter
from app.models.paragraph import Paragraph
from app.models.test import Test, Question, QuestionOption, QuestionType, DifficultyLevel
from app.models.teacher import Teacher
from app.models.student import Student
from app.models.school_class import SchoolClass
from app.models.invitation_code import InvitationCode
from app.models.goso import Subject
from app.core.security import get_password_hash

# Production DATABASE_URL с ai_mentor_user (superuser) для обхода RLS
# Используются переменные окружения из docker-compose
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "ai_mentor_db")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "ai_mentor_pass")

# ВАЖНО: Используем ai_mentor_user (SUPERUSER) для обхода RLS политик
DATABASE_URL = f"postgresql+asyncpg://ai_mentor_user:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"


async def seed_database():
    """Заполнить базу данных тестовыми данными для production."""
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        print("🌱 Начинаем заполнение PRODUCTION базы данных...")
        print("=" * 60)
        print(f"🔗 Database: {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")
        print(f"👤 User: ai_mentor_user (SUPERUSER)")
        print("=" * 60)
        print()

        # ========================================
        # 1. Создаем администраторов
        # ========================================
        print("👑 Создание администраторов...")

        # SUPER_ADMIN
        result = await session.execute(
            select(User).where(User.email == "superadmin@aimentor.com")
        )
        super_admin = result.scalar_one_or_none()

        if not super_admin:
            super_admin = User(
                email="superadmin@aimentor.com",
                password_hash=get_password_hash("admin123"),
                first_name="Супер",
                last_name="Администратор",
                role=UserRole.SUPER_ADMIN,
                school_id=None,  # SUPER_ADMIN не привязан к школе
                is_active=True,
                is_verified=True,
            )
            session.add(super_admin)
            await session.flush()
            print("  ✅ SUPER_ADMIN: superadmin@aimentor.com / admin123")
        else:
            print("  ⏭️  SUPER_ADMIN уже существует")

        await session.commit()
        print()

        # ========================================
        # 2. Создаем школу
        # ========================================
        print("🏫 Создание школы...")

        result = await session.execute(
            select(School).where(School.code == "SCHOOL001")
        )
        school = result.scalar_one_or_none()

        if not school:
            school = School(
                name="Тестовая школа №1",
                code="SCHOOL001",
                address="г. Алматы, ул. Тестовая, д. 1",
                phone="+7 (727) 123-45-67",
                email="school001@edu.kz",
                description="Тестовая школа для демонстрации платформы AI Mentor",
                is_active=True,
            )
            session.add(school)
            await session.flush()
            print(f"  ✅ Школа: {school.name} (код: {school.code})")
        else:
            print(f"  ⏭️  Школа {school.code} уже существует")

        await session.commit()
        print()

        # School ADMIN
        print("👨‍💼 Создание школьного администратора...")

        result = await session.execute(
            select(User).where(User.email == "school.admin@test.com")
        )
        school_admin = result.scalar_one_or_none()

        if not school_admin:
            school_admin = User(
                email="school.admin@test.com",
                password_hash=get_password_hash("admin123"),
                first_name="Айгуль",
                last_name="Сатыбалдиева",
                role=UserRole.ADMIN,
                school_id=school.id,
                is_active=True,
                is_verified=True,
            )
            session.add(school_admin)
            await session.flush()
            print(f"  ✅ School ADMIN: school.admin@test.com / admin123 (школа: {school.name})")
        else:
            print("  ⏭️  School ADMIN уже существует")

        await session.commit()
        print()

        # ========================================
        # 2.1 Создаем публичную школу
        # ========================================
        print("🌐 Создание публичной школы...")

        result = await session.execute(
            select(School).where(School.code == "AIMENTOR_PUBLIC")
        )
        public_school = result.scalar_one_or_none()

        if not public_school:
            public_school = School(
                name="AI Mentor Public",
                code="AIMENTOR_PUBLIC",
                address="Online",
                phone=None,
                email="public@ai-mentor.kz",
                description="Публичная школа для самостоятельного обучения без привязки к учебному заведению",
                is_active=True,
            )
            session.add(public_school)
            await session.flush()
            print(f"  ✅ Публичная школа: {public_school.name} (код: {public_school.code})")
        else:
            print(f"  ⏭️  Публичная школа уже существует")

        await session.commit()
        print()

        # ========================================
        # Загружаем справочник предметов
        # ========================================
        result = await session.execute(select(Subject))
        subjects = result.scalars().all()
        subject_lookup = {}
        for subj in subjects:
            subject_lookup[subj.name_ru.lower()] = subj.id
            subject_lookup[subj.name_kz.lower()] = subj.id
        print(f"📋 Загружено {len(subjects)} предметов в справочнике")
        print()

        # ========================================
        # 3. Создаем глобальные учебники
        # ========================================
        print("📚 Создание глобальных учебников...")
        textbooks_data = [
            {
                "title": "Математика 7 класс",
                "subject": "Математика",
                "grade_level": 7,
                "description": "Алгебра и начала анализа для 7 класса",
                "chapters": [
                    {
                        "title": "Линейные уравнения",
                        "chapter_number": 1,
                        "paragraphs": [
                            {"title": "Понятие уравнения", "content": "Уравнение - это математическое равенство с неизвестными..."},
                            {"title": "Решение простых уравнений", "content": "Для решения уравнения ax + b = 0 необходимо..."},
                        ]
                    },
                    {
                        "title": "Системы уравнений",
                        "chapter_number": 2,
                        "paragraphs": [
                            {"title": "Метод подстановки", "content": "Метод подстановки заключается в..."},
                        ]
                    },
                ]
            },
            {
                "title": "Физика 8 класс",
                "subject": "Физика",
                "grade_level": 8,
                "description": "Основы механики и термодинамики",
                "chapters": [
                    {
                        "title": "Механическое движение",
                        "chapter_number": 1,
                        "paragraphs": [
                            {"title": "Скорость и ускорение", "content": "Скорость - это физическая величина..."},
                            {"title": "Законы Ньютона", "content": "Первый закон Ньютона гласит..."},
                        ]
                    },
                ]
            },
            {
                "title": "Химия 9 класс",
                "subject": "Химия",
                "grade_level": 9,
                "description": "Неорганическая химия",
                "chapters": [
                    {
                        "title": "Периодическая таблица",
                        "chapter_number": 1,
                        "paragraphs": [
                            {"title": "Структура атома", "content": "Атом состоит из протонов, нейтронов и электронов..."},
                        ]
                    },
                ]
            },
            {
                "title": "Биология 8 класс",
                "subject": "Биология",
                "grade_level": 8,
                "description": "Анатомия человека",
                "chapters": [
                    {
                        "title": "Системы органов",
                        "chapter_number": 1,
                        "paragraphs": [
                            {"title": "Кровеносная система", "content": "Сердце и сосуды образуют кровеносную систему..."},
                        ]
                    },
                ]
            },
            {
                "title": "История Казахстана 10 класс",
                "subject": "История",
                "grade_level": 10,
                "description": "История Казахстана с древних времен",
                "chapters": [
                    {
                        "title": "Древний Казахстан",
                        "chapter_number": 1,
                        "paragraphs": [
                            {"title": "Сакские племена", "content": "Саки - древние кочевые племена на территории Казахстана..."},
                        ]
                    },
                ]
            },
            {
                "title": "Геометрия 9 класс",
                "subject": "Математика",
                "grade_level": 9,
                "description": "Планиметрия и стереометрия",
                "chapters": [
                    {
                        "title": "Треугольники",
                        "chapter_number": 1,
                        "paragraphs": [
                            {"title": "Виды треугольников", "content": "Треугольники бывают равносторонние, равнобедренные..."},
                        ]
                    },
                ]
            },
        ]

        created_textbooks = []
        for tb_data in textbooks_data:
            # Проверяем, существует ли учебник
            result = await session.execute(
                select(Textbook).where(Textbook.title == tb_data["title"])
            )
            textbook = result.scalar_one_or_none()

            if not textbook:
                # Lookup subject_id by name
                subject_name = tb_data["subject"]
                subject_id = subject_lookup.get(subject_name.lower())

                textbook = Textbook(
                    title=tb_data["title"],
                    subject_id=subject_id,  # FK to subjects table
                    subject=subject_name,   # Text for backward compatibility
                    grade_level=tb_data["grade_level"],
                    description=tb_data["description"],
                    school_id=None,  # Глобальный контент
                    is_customized=False,
                    is_active=True,
                )
                session.add(textbook)
                await session.flush()

                # Создаем главы
                for ch_data in tb_data["chapters"]:
                    chapter = Chapter(
                        textbook_id=textbook.id,
                        title=ch_data["title"],
                        number=ch_data["chapter_number"],
                        order=ch_data["chapter_number"],
                    )
                    session.add(chapter)
                    await session.flush()

                    # Создаем параграфы
                    for idx, par_data in enumerate(ch_data["paragraphs"], 1):
                        paragraph = Paragraph(
                            chapter_id=chapter.id,
                            title=par_data["title"],
                            number=idx,
                            order=idx,
                            content=par_data["content"],
                        )
                        session.add(paragraph)

                print(f"  ✅ {textbook.title}")
            else:
                print(f"  ⏭️  {textbook.title} (уже существует)")

            created_textbooks.append(textbook)

        await session.commit()
        print(f"✅ Создано {len(created_textbooks)} учебников с главами и параграфами")
        print()

        # ========================================
        # 4. Создаем глобальные тесты
        # ========================================
        print("📝 Создание глобальных тестов...")
        tests_data = [
            {
                "title": "Математика 7 класс - Линейные уравнения",
                "description": "Проверка знаний по теме линейных уравнений",
                "subject": "Математика",
                "grade_level": 7,
                "questions": [
                    {
                        "text": "Решите уравнение: 2x + 5 = 13",
                        "type": QuestionType.SINGLE_CHOICE,
                        "difficulty": DifficultyLevel.EASY,
                        "options": [
                            {"text": "x = 4", "is_correct": True},
                            {"text": "x = 3", "is_correct": False},
                            {"text": "x = 5", "is_correct": False},
                            {"text": "x = 2", "is_correct": False},
                        ]
                    },
                    {
                        "text": "Какое из утверждений верно для уравнения ax = b?",
                        "type": QuestionType.MULTIPLE_CHOICE,
                        "difficulty": DifficultyLevel.MEDIUM,
                        "options": [
                            {"text": "Если a = 0 и b ≠ 0, уравнение не имеет решений", "is_correct": True},
                            {"text": "Если a ≠ 0, решение x = b/a", "is_correct": True},
                            {"text": "Уравнение всегда имеет решение", "is_correct": False},
                        ]
                    },
                ]
            },
            {
                "title": "Физика 8 класс - Механика",
                "description": "Основные законы механики",
                "subject": "Физика",
                "grade_level": 8,
                "questions": [
                    {
                        "text": "Первый закон Ньютона также называется законом...",
                        "type": QuestionType.SINGLE_CHOICE,
                        "difficulty": DifficultyLevel.EASY,
                        "options": [
                            {"text": "инерции", "is_correct": True},
                            {"text": "гравитации", "is_correct": False},
                            {"text": "сохранения энергии", "is_correct": False},
                        ]
                    },
                    {
                        "text": "Скорость - это векторная величина",
                        "type": QuestionType.TRUE_FALSE,
                        "difficulty": DifficultyLevel.EASY,
                        "options": [
                            {"text": "Верно", "is_correct": True},
                            {"text": "Неверно", "is_correct": False},
                        ]
                    },
                ]
            },
            {
                "title": "Биология 8 класс - Анатомия",
                "description": "Строение тела человека",
                "subject": "Биология",
                "grade_level": 8,
                "questions": [
                    {
                        "text": "Сколько камер в сердце человека?",
                        "type": QuestionType.SINGLE_CHOICE,
                        "difficulty": DifficultyLevel.MEDIUM,
                        "options": [
                            {"text": "4", "is_correct": True},
                            {"text": "2", "is_correct": False},
                            {"text": "3", "is_correct": False},
                            {"text": "5", "is_correct": False},
                        ]
                    },
                ]
            },
        ]

        created_tests = []
        for test_data in tests_data:
            # Проверяем, существует ли тест
            result = await session.execute(
                select(Test).where(Test.title == test_data["title"])
            )
            test = result.scalar_one_or_none()

            if not test:
                test = Test(
                    title=test_data["title"],
                    description=test_data["description"],
                    difficulty=DifficultyLevel.MEDIUM,
                    school_id=None,  # Глобальный тест
                    is_active=True,
                    time_limit=45,
                    passing_score=70.0,
                )
                session.add(test)
                await session.flush()

                # Создаем вопросы
                for q_idx, q_data in enumerate(test_data["questions"], 1):
                    question = Question(
                        test_id=test.id,
                        order=q_idx,
                        question_text=q_data["text"],
                        question_type=q_data["type"],
                        points=10.0,
                    )
                    session.add(question)
                    await session.flush()

                    # Создаем варианты ответов
                    for opt_idx, opt_data in enumerate(q_data["options"], 1):
                        option = QuestionOption(
                            question_id=question.id,
                            order=opt_idx,
                            option_text=opt_data["text"],
                            is_correct=opt_data["is_correct"],
                        )
                        session.add(option)

                print(f"  ✅ {test.title} ({len(test_data['questions'])} вопросов)")
            else:
                print(f"  ⏭️  {test.title} (уже существует)")

            created_tests.append(test)

        await session.commit()
        print(f"✅ Создано {len(created_tests)} глобальных тестов")
        print()

        # ========================================
        # 5. Создаем учителей
        # ========================================
        print("👨‍🏫 Создание учителей...")
        teachers_data = [
            {"email": "teacher.math@school001.com", "first_name": "Айгерим", "last_name": "Нурсултанова", "middle_name": "Ермековна", "subject": "Математика"},
            {"email": "teacher.physics@school001.com", "first_name": "Асхат", "last_name": "Жумабаев", "middle_name": "Канатович", "subject": "Физика"},
            {"email": "teacher.chemistry@school001.com", "first_name": "Динара", "last_name": "Сатыбалдиева", "middle_name": "Тимуровна", "subject": "Химия"},
            {"email": "teacher.biology@school001.com", "first_name": "Нургуль", "last_name": "Абишева", "middle_name": "Сериковна", "subject": "Биология"},
            {"email": "teacher.history@school001.com", "first_name": "Ержан", "last_name": "Кенжебаев", "middle_name": "Алмасович", "subject": "История"},
        ]

        created_teachers = []
        for teacher_data in teachers_data:
            # Проверяем, существует ли user
            result = await session.execute(
                select(User).where(User.email == teacher_data["email"])
            )
            user = result.scalar_one_or_none()

            if not user:
                # Создаем User
                user = User(
                    email=teacher_data["email"],
                    password_hash=get_password_hash("teacher123"),
                    first_name=teacher_data["first_name"],
                    last_name=teacher_data["last_name"],
                    middle_name=teacher_data.get("middle_name"),
                    role=UserRole.TEACHER,
                    school_id=school.id,
                    is_active=True,
                    is_verified=True,
                )
                session.add(user)
                await session.flush()

                # Создаем Teacher
                subject_name = teacher_data["subject"]
                subject_id = subject_lookup.get(subject_name.lower())

                teacher = Teacher(
                    school_id=school.id,
                    user_id=user.id,
                    teacher_code=f"T{school.id:03d}{len(created_teachers)+1:03d}",
                    subject_id=subject_id,  # FK to subjects table
                    subject=subject_name,   # Text for backward compatibility
                )
                session.add(teacher)
                await session.flush()

                print(f"  ✅ {user.first_name} {user.last_name} ({subject_name})")
            else:
                print(f"  ⏭️  {user.email} (уже существует)")
                # Получаем teacher
                result = await session.execute(
                    select(Teacher).where(Teacher.user_id == user.id)
                )
                teacher = result.scalar_one_or_none()

            if teacher:
                created_teachers.append(teacher)

        await session.commit()
        print(f"✅ Создано {len(created_teachers)} учителей")
        print()

        # ========================================
        # 6. Создаем учеников
        # ========================================
        print("👨‍🎓 Создание учеников...")
        students_data = [
            {"email": "student1@school001.com", "first_name": "Алихан", "last_name": "Султанов", "grade": 7, "birth_date": "2012-03-15"},
            {"email": "student2@school001.com", "first_name": "Аружан", "last_name": "Есимова", "grade": 7, "birth_date": "2012-07-22"},
            {"email": "student3@school001.com", "first_name": "Нурислам", "last_name": "Бекжанов", "grade": 8, "birth_date": "2011-01-10"},
            {"email": "student4@school001.com", "first_name": "Жанель", "last_name": "Кабдулова", "grade": 8, "birth_date": "2011-09-05"},
            {"email": "student5@school001.com", "first_name": "Данияр", "last_name": "Мухамедов", "grade": 9, "birth_date": "2010-11-28"},
            {"email": "student6@school001.com", "first_name": "Айым", "last_name": "Сейдахметова", "grade": 9, "birth_date": "2010-04-17"},
            {"email": "student7@school001.com", "first_name": "Ернар", "last_name": "Токаев", "grade": 10, "birth_date": "2009-08-03"},
            {"email": "student8@school001.com", "first_name": "Камила", "last_name": "Нурланова", "grade": 10, "birth_date": "2009-12-20"},
        ]

        created_students = []
        for student_data in students_data:
            # Проверяем, существует ли user
            result = await session.execute(
                select(User).where(User.email == student_data["email"])
            )
            user = result.scalar_one_or_none()

            if not user:
                # Создаем User
                user = User(
                    email=student_data["email"],
                    password_hash=get_password_hash("student123"),
                    first_name=student_data["first_name"],
                    last_name=student_data["last_name"],
                    role=UserRole.STUDENT,
                    school_id=school.id,
                    is_active=True,
                    is_verified=True,
                )
                session.add(user)
                await session.flush()

                # Создаем Student
                student = Student(
                    school_id=school.id,
                    user_id=user.id,
                    student_code=f"S{school.id:03d}{len(created_students)+1:04d}",
                    grade_level=student_data["grade"],
                    birth_date=date.fromisoformat(student_data["birth_date"]),
                )
                session.add(student)
                await session.flush()

                print(f"  ✅ {user.first_name} {user.last_name} ({student_data['grade']} класс)")
            else:
                print(f"  ⏭️  {user.email} (уже существует)")
                # Получаем student
                result = await session.execute(
                    select(Student).where(Student.user_id == user.id)
                )
                student = result.scalar_one_or_none()

            if student:
                created_students.append(student)

        await session.commit()
        print(f"✅ Создано {len(created_students)} учеников")
        print()

        # ========================================
        # 7. Создаем классы
        # ========================================
        print("🏫 Создание классов...")
        classes_data = [
            {"name": "7-А", "grade_level": 7, "teacher_idx": 0},  # Математика
            {"name": "8-Б", "grade_level": 8, "teacher_idx": 1},  # Физика
            {"name": "9-В", "grade_level": 9, "teacher_idx": 2},  # Химия
            {"name": "10-А", "grade_level": 10, "teacher_idx": 4},  # История
        ]

        created_classes = []
        for class_data in classes_data:
            # Проверяем, существует ли класс
            result = await session.execute(
                select(SchoolClass).where(
                    SchoolClass.name == class_data["name"],
                    SchoolClass.school_id == school.id
                )
            )
            school_class = result.scalar_one_or_none()

            if not school_class:
                teacher = created_teachers[class_data["teacher_idx"]] if class_data["teacher_idx"] < len(created_teachers) else None

                school_class = SchoolClass(
                    school_id=school.id,
                    name=class_data["name"],
                    code=class_data["name"],  # Используем имя как код
                    grade_level=class_data["grade_level"],
                    academic_year="2024-2025",
                )
                session.add(school_class)
                await session.flush()

                print(f"  ✅ {class_data['name']}")
            else:
                print(f"  ⏭️  {class_data['name']} (уже существует)")

            created_classes.append(school_class)

        await session.commit()
        print(f"✅ Создано {len(created_classes)} классов")
        print()

        # ========================================
        # 8. Связываем учеников с классами
        # ========================================
        print("🔗 Связывание учеников с классами...")
        # 7А: студенты 0-1 (grade 7)
        # 8Б: студенты 2-3 (grade 8)
        # 9В: студенты 4-5 (grade 9)
        # 10А: студенты 6-7 (grade 10)

        class_assignments = [
            (0, [0, 1]),  # 7А
            (1, [2, 3]),  # 8Б
            (2, [4, 5]),  # 9В
            (3, [6, 7]),  # 10А
        ]

        # Связываем через raw SQL для обхода lazy loading
        from app.models.school_class import class_students
        for class_idx, student_indices in class_assignments:
            if class_idx < len(created_classes):
                school_class = created_classes[class_idx]
                count = 0
                for student_idx in student_indices:
                    if student_idx < len(created_students):
                        student = created_students[student_idx]

                        # Проверяем, не добавлен ли уже студент в класс
                        result = await session.execute(
                            select(class_students).where(
                                class_students.c.class_id == school_class.id,
                                class_students.c.student_id == student.id
                            )
                        )
                        existing = result.first()

                        if not existing:
                            # Вставляем напрямую в таблицу связей
                            await session.execute(
                                class_students.insert().values(
                                    class_id=school_class.id,
                                    student_id=student.id
                                )
                            )
                            count += 1

                if count > 0:
                    print(f"  ✅ {school_class.name}: {count} учеников добавлено")
                else:
                    print(f"  ⏭️  {school_class.name}: ученики уже распределены")

        await session.commit()
        print("✅ Ученики распределены по классам")
        print()

        # ========================================
        # 9. Создаем публичные коды приглашения
        # ========================================
        print("🎫 Создание публичных кодов приглашения...")

        public_codes_data = [
            {"code": "PUBLIC7", "grade_level": 7},
            {"code": "PUBLIC8", "grade_level": 8},
            {"code": "PUBLIC9", "grade_level": 9},
            {"code": "PUBLIC10", "grade_level": 10},
            {"code": "PUBLIC11", "grade_level": 11},
        ]

        created_codes_count = 0
        for code_data in public_codes_data:
            result = await session.execute(
                select(InvitationCode).where(InvitationCode.code == code_data["code"])
            )
            existing_code = result.scalar_one_or_none()

            if not existing_code:
                invitation_code = InvitationCode(
                    code=code_data["code"],
                    school_id=public_school.id,
                    class_id=None,  # Без привязки к классу
                    grade_level=code_data["grade_level"],
                    expires_at=None,  # Никогда не истекает
                    max_uses=None,  # Неограниченное использование
                    created_by=super_admin.id,
                    is_active=True,
                    uses_count=0,
                )
                session.add(invitation_code)
                created_codes_count += 1
                print(f"  ✅ Код: {code_data['code']} ({code_data['grade_level']} класс)")
            else:
                print(f"  ⏭️  Код {code_data['code']} уже существует")

        await session.commit()
        print(f"✅ Создано {created_codes_count} публичных кодов")
        print()

        # ========================================
        # Итоговая статистика
        # ========================================
        print("=" * 60)
        print("🎉 Заполнение PRODUCTION базы данных завершено!")
        print("=" * 60)
        print(f"👑 Администраторы:")
        print(f"   - SUPER_ADMIN: superadmin@aimentor.com")
        print(f"   - School ADMIN: school.admin@test.com")
        print()
        print(f"🏫 Школа: {school.name} (код: {school.code})")
        print()
        print(f"📚 Учебников (глобальных): {len(created_textbooks)}")
        print(f"📝 Тестов (глобальных): {len(created_tests)}")
        print(f"👨‍🏫 Учителей: {len(created_teachers)}")
        print(f"👨‍🎓 Учеников: {len(created_students)}")
        print(f"🏫 Классов: {len(created_classes)}")
        print()
        print("🔐 Учетные данные:")
        print("   Администраторы: пароль admin123")
        print("   Учителя: пароль teacher123")
        print("   Ученики: пароль student123")
        print()
        print("⚠️  ВАЖНО: Смените пароли после деплоя!")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(seed_database())
