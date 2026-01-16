"""
Скрипт для создания тестов по Қазақстан тарихы (XVIII-XIX ғғ.) для 7 класса.

Создает 3 теста на казахском языке:
1. Қазақ-жоңғар соғыстары (Глава 1) - 10 вопросов
2. Абылай хан дәуірі (Глава 2) - 8 вопросов
3. XVIII ғасырдағы мәдениет (Глава 3) - 6 вопросов

Запуск:
    cd backend
    python seed_tests_kz_history.py
"""
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select

from app.models.test import Test, Question, QuestionOption, QuestionType, DifficultyLevel, TestPurpose

# Database configuration
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "ai_mentor_db")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "AiM3nt0rPr0dS3cur3Passw0rd2025")

DATABASE_URL = f"postgresql+asyncpg://ai_mentor_user:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Textbook and chapter IDs (based on textbook_id=15)
TEXTBOOK_ID = 15
CHAPTER_1_ID = 54  # ҚАЗАҚ-ЖОҢҒАР СОҒЫСТАРЫ
CHAPTER_2_ID = 55  # XVIII ҒАСЫРДАҒЫ ҚАЗАҚ ХАНДЫҒЫ
CHAPTER_3_ID = 56  # XVIII ҒАСЫРДАҒЫ ҚАЗАҚСТАН МӘДЕНИЕТІ


# ============================================================
# ТЕСТ 1: Қазақ-жоңғар соғыстары (10 вопросов)
# ============================================================
TEST_1_DATA = {
    "title": "Қазақ-жоңғар соғыстары",
    "description": "XVIII ғасырдағы қазақ-жоңғар соғыстары бойынша тест. §1-6 параграфтар материалдары.",
    "chapter_id": CHAPTER_1_ID,
    "questions": [
        {
            "question_text": "«Жеті жарғы» заңдар жинағын қай хан жарыққа шығарды?",
            "question_type": QuestionType.SINGLE_CHOICE,
            "explanation": "Тәуке хан «Қасым ханның қасқа жолы» және «Есім ханның ескі жолы» заңдарын негізге ала отырып, «Жеті жарғы» заңдар жинағын жарыққа шығарды.",
            "options": [
                {"text": "Тәуке хан", "is_correct": True},
                {"text": "Абылай хан", "is_correct": False},
                {"text": "Әбілқайыр хан", "is_correct": False},
                {"text": "Қайып хан", "is_correct": False},
            ]
        },
        {
            "question_text": "1710 жылы қазақ жүздерінің өкілдері қай жерде жиналды?",
            "question_type": QuestionType.SINGLE_CHOICE,
            "explanation": "1710 жылы қазақ жүздерінің белгілі өкілдері Қарақұм маңында бас қосып, жоңғарларға соққы берудің мүмкіндіктерін талқылады.",
            "options": [
                {"text": "Қарақұм", "is_correct": True},
                {"text": "Ордабасы", "is_correct": False},
                {"text": "Түркістан", "is_correct": False},
                {"text": "Аягөз", "is_correct": False},
            ]
        },
        {
            "question_text": "«Ақтабан шұбырынды» оқиғасы қай жылы басталды?",
            "question_type": QuestionType.SINGLE_CHOICE,
            "explanation": "1723 жыл қазақ халқы үшін өте қиын кезеңнің бастамасы болды. Осы жылы «Ақтабан шұбырынды, Алқакөл сұлама» басталды.",
            "options": [
                {"text": "1723 жыл", "is_correct": True},
                {"text": "1718 жыл", "is_correct": False},
                {"text": "1720 жыл", "is_correct": False},
                {"text": "1730 жыл", "is_correct": False},
            ]
        },
        {
            "question_text": "Ордабасы жиынында үш жүз әскерінің бас қолбасшысы болып кім тағайындалды?",
            "question_type": QuestionType.SINGLE_CHOICE,
            "explanation": "1726 жылғы Ордабасы жиынында Әбілқайыр ханды қазақтың үш жүзіне бас қолбасшы етіп тағайындады.",
            "options": [
                {"text": "Әбілқайыр хан", "is_correct": True},
                {"text": "Абылай хан", "is_correct": False},
                {"text": "Бөгенбай батыр", "is_correct": False},
                {"text": "Қабанбай батыр", "is_correct": False},
            ]
        },
        {
            "question_text": "Аңырақай шайқасы қай жылы болды?",
            "question_type": QuestionType.SINGLE_CHOICE,
            "explanation": "Аңырақай шайқасы 1730 жылдың көктемінде Балқаш көлінің оңтүстігіндегі Итішпес деген жерде өтті.",
            "options": [
                {"text": "1730 жыл", "is_correct": True},
                {"text": "1728 жыл", "is_correct": False},
                {"text": "1735 жыл", "is_correct": False},
                {"text": "1740 жыл", "is_correct": False},
            ]
        },
        {
            "question_text": "Аңырақай шайқасында ерекше көзге түскен жас сұлтан кім?",
            "question_type": QuestionType.SINGLE_CHOICE,
            "explanation": "Ұрыс басында жекпе-жекке шығып, он екі жоңғарды аттан шауып түсірген жас Әбілмансұр сұлтан ерекше көзге түсті. Осыдан соң ол ел арасында Абылай атанып кетті.",
            "options": [
                {"text": "Әбілмансұр (Абылай)", "is_correct": True},
                {"text": "Қайып", "is_correct": False},
                {"text": "Болат", "is_correct": False},
                {"text": "Нұралы", "is_correct": False},
            ]
        },
        {
            "question_text": "Қазақтың үш биі қайсылары?",
            "question_type": QuestionType.MULTIPLE_CHOICE,
            "explanation": "Төле би, Қазыбек би және Әйтеке би — қазақтың үш биі ретінде танылған, жоңғарларға қарсы күресте және халық бірлігін нығайтуда үлкен рөл атқарған.",
            "options": [
                {"text": "Төле би", "is_correct": True},
                {"text": "Қазыбек би", "is_correct": True},
                {"text": "Әйтеке би", "is_correct": True},
                {"text": "Бұхар жырау", "is_correct": False},
            ]
        },
        {
            "question_text": "Қалмаққырылған (Бұланты) шайқасы 1728 жылы болды.",
            "question_type": QuestionType.TRUE_FALSE,
            "explanation": "1728 жылы Бұланты және Білеуті өзендері аралығында біріккен қазақ жасағы жоңғарларға ойсырата соққы берді.",
            "options": [
                {"text": "Дұрыс", "is_correct": True},
                {"text": "Бұрыс", "is_correct": False},
            ]
        },
        {
            "question_text": "Жоңғар хандығы Қазақ хандығының батысында орналасқан.",
            "question_type": QuestionType.TRUE_FALSE,
            "explanation": "Жоңғар хандығы Қазақ хандығының шығысында орналасқан, батысында емес.",
            "options": [
                {"text": "Дұрыс", "is_correct": False},
                {"text": "Бұрыс", "is_correct": True},
            ]
        },
        {
            "question_text": "Бұланты шайқасында қазақ қолы қанша адамнан тұрды?",
            "question_type": QuestionType.SINGLE_CHOICE,
            "explanation": "Бұл шайқас қазақ-қырғыз және басқа халықтардың 60 мыңдық қолының толық жеңісімен аяқталды.",
            "options": [
                {"text": "60 мың", "is_correct": True},
                {"text": "30 мың", "is_correct": False},
                {"text": "40 мың", "is_correct": False},
                {"text": "80 мың", "is_correct": False},
            ]
        },
    ]
}


# ============================================================
# ТЕСТ 2: Абылай хан дәуірі (8 вопросов)
# ============================================================
TEST_2_DATA = {
    "title": "XVIII ғасырдағы Қазақ хандығы: Абылай хан дәуірі",
    "description": "XVIII ғасырдағы Қазақ хандығы, Әбілқайыр хан мен Абылай ханның саясаты. §7-14 параграфтар материалдары.",
    "chapter_id": CHAPTER_2_ID,
    "questions": [
        {
            "question_text": "Әбілқайыр хан Ресей бодандығын қабылдау туралы өтініш қай жылы жіберді?",
            "question_type": QuestionType.SINGLE_CHOICE,
            "explanation": "1730 жылы Әбілқайыр келіссөз жүргізіп, Ресей патшайымы Анна Иоанновнаға бодандық туралы өтініш жіберді.",
            "options": [
                {"text": "1730 жыл", "is_correct": True},
                {"text": "1725 жыл", "is_correct": False},
                {"text": "1735 жыл", "is_correct": False},
                {"text": "1740 жыл", "is_correct": False},
            ]
        },
        {
            "question_text": "Абылай хан қай жылы дүниеге келді?",
            "question_type": QuestionType.SINGLE_CHOICE,
            "explanation": "Абылай (Әбілмансұр) 1711 жылы дүниеге келген.",
            "options": [
                {"text": "1711 жыл", "is_correct": True},
                {"text": "1700 жыл", "is_correct": False},
                {"text": "1720 жыл", "is_correct": False},
                {"text": "1730 жыл", "is_correct": False},
            ]
        },
        {
            "question_text": "Абылай бүкіл қазақтың ханы болып қай жылы сайланды?",
            "question_type": QuestionType.SINGLE_CHOICE,
            "explanation": "1771 жылы Түркістанда үш жүздің өкілдері жиналып, Абылайды ақ киізге отырғызып, бүкіл қазақтың ханы етіп сайлады.",
            "options": [
                {"text": "1771 жыл", "is_correct": True},
                {"text": "1765 жыл", "is_correct": False},
                {"text": "1770 жыл", "is_correct": False},
                {"text": "1778 жыл", "is_correct": False},
            ]
        },
        {
            "question_text": "Омбы бекінісінің негізі қай жылы қаланды?",
            "question_type": QuestionType.SINGLE_CHOICE,
            "explanation": "1716 жылы 20 мамырда Омбы бекінісінің негізі қаланды.",
            "options": [
                {"text": "1716 жыл", "is_correct": True},
                {"text": "1715 жыл", "is_correct": False},
                {"text": "1720 жыл", "is_correct": False},
                {"text": "1725 жыл", "is_correct": False},
            ]
        },
        {
            "question_text": "1731 жылы Кіші жүз қазақтарының Ресейге ант беруіне кім басшылық жасады?",
            "question_type": QuestionType.SINGLE_CHOICE,
            "explanation": "1731 жылдың қазан айында Әбілқайыр мен оны қолдаған Кіші жүздің 29 старшыны Ресейге ант берді.",
            "options": [
                {"text": "Әбілқайыр хан", "is_correct": True},
                {"text": "Абылай хан", "is_correct": False},
                {"text": "Әбілмәмбет хан", "is_correct": False},
                {"text": "Тәуке хан", "is_correct": False},
            ]
        },
        {
            "question_text": "«Шүршітқырылған» деп аталған жер қайда орналасқан?",
            "question_type": QuestionType.SINGLE_CHOICE,
            "explanation": "Баянауыл маңындағы Шідерті өзенінің бойында қазақтар Цин әскеріне ауыр соққы берді, бұл жер «Шүршітқырылған» деп аталды.",
            "options": [
                {"text": "Баянауыл маңында, Шідерті өзені бойында", "is_correct": True},
                {"text": "Балқаш көлі маңында", "is_correct": False},
                {"text": "Түркістан маңында", "is_correct": False},
                {"text": "Орынбор маңында", "is_correct": False},
            ]
        },
        {
            "question_text": "Жоңғария мемлекеті қай жылы құлады?",
            "question_type": QuestionType.SINGLE_CHOICE,
            "explanation": "1755 жылы Цин империясы Жоңғарияға әскер аттандырып, 1757-1758 жылдары жоңғарларды біржолата талқандады.",
            "options": [
                {"text": "1757-1758 жылдары", "is_correct": True},
                {"text": "1750-1751 жылдары", "is_correct": False},
                {"text": "1760-1761 жылдары", "is_correct": False},
                {"text": "1745-1746 жылдары", "is_correct": False},
            ]
        },
        {
            "question_text": "Абылай хан Ресей мен Қытай империялары арасында теңгерімді саясат ұстанды.",
            "question_type": QuestionType.TRUE_FALSE,
            "explanation": "Абылай Ресей мен Қытай империялары арасында теңгерімді саясат ұстанып, елдің тәуелсіздігін сақтап қалуға тырысты.",
            "options": [
                {"text": "Дұрыс", "is_correct": True},
                {"text": "Бұрыс", "is_correct": False},
            ]
        },
    ]
}


# ============================================================
# ТЕСТ 3: XVIII ғасырдағы мәдениет (6 вопросов)
# ============================================================
TEST_3_DATA = {
    "title": "XVIII ғасырдағы Қазақстан мәдениеті",
    "description": "XVIII ғасырдағы қазақ мәдениеті: ақын-жыраулар, салт-дәстүр, қолөнер, ұлттық киімдер. §15-18 параграфтар материалдары.",
    "chapter_id": CHAPTER_3_ID,
    "questions": [
        {
            "question_text": "Бұқар жырау қай жылдары өмір сүрді?",
            "question_type": QuestionType.SINGLE_CHOICE,
            "explanation": "Бұқар жырау (1668-1781) — Тәуке ханның биі, Абылайдың кеңесшісі болған.",
            "options": [
                {"text": "1668-1781", "is_correct": True},
                {"text": "1650-1750", "is_correct": False},
                {"text": "1700-1780", "is_correct": False},
                {"text": "1680-1760", "is_correct": False},
            ]
        },
        {
            "question_text": "«Жеті ата» ұғымының мәні неде?",
            "question_type": QuestionType.SINGLE_CHOICE,
            "explanation": "Қазақ халқында жеті атаға дейін бірдей адамдар жақын туыс саналады. Бұл тәртіп елдің бірлігін сақтаумен қатар, жеті атаға дейін қыз алыспау (экзогамия) дәстүрін қалыптастырды.",
            "options": [
                {"text": "Жеті атаға дейін қыз алыспау", "is_correct": True},
                {"text": "Жеті атаға дейін туыс емес", "is_correct": False},
                {"text": "Жеті атаға дейін ел бастау", "is_correct": False},
                {"text": "Жеті атаға дейін би болу", "is_correct": False},
            ]
        },
        {
            "question_text": "Ақтамберді жырау қай жылдары өмір сүрді?",
            "question_type": QuestionType.SINGLE_CHOICE,
            "explanation": "Ақтамберді жырау (1675-1768) — жоңғарларға қарсы шайқастарға қатысқан батыр-жырау.",
            "options": [
                {"text": "1675-1768", "is_correct": True},
                {"text": "1668-1781", "is_correct": False},
                {"text": "1650-1750", "is_correct": False},
                {"text": "1700-1780", "is_correct": False},
            ]
        },
        {
            "question_text": "«Сәукеле» деген не?",
            "question_type": QuestionType.SINGLE_CHOICE,
            "explanation": "Сәукеле — ерекше қымбат, ұзатылатын қыз киетін бас киім.",
            "options": [
                {"text": "Ұзатылатын қызға арналған бас киім", "is_correct": True},
                {"text": "Еркек адамға арналған бас киім", "is_correct": False},
                {"text": "Балаларға арналған киім", "is_correct": False},
                {"text": "Қыс мезгіліне арналған сырт киім", "is_correct": False},
            ]
        },
        {
            "question_text": "Қазақ зергерлері қандай металдардан әшекей бұйымдар жасады?",
            "question_type": QuestionType.MULTIPLE_CHOICE,
            "explanation": "Зергерлер күміс пен алтыннан әшекей бұйымдар (білезік, сырға, жүзік) соққан, ер-тұрманды сәндеген.",
            "options": [
                {"text": "Күміс", "is_correct": True},
                {"text": "Алтын", "is_correct": True},
                {"text": "Мыс", "is_correct": False},
                {"text": "Темір", "is_correct": False},
            ]
        },
        {
            "question_text": "Наурыз мейрамы — жыл басы, Ұлыстың ұлы күні.",
            "question_type": QuestionType.TRUE_FALSE,
            "explanation": "Наурыз мейрамы — жыл басы, Ұлыстың ұлы күні. Халқымыз наурызкөже дайындап, бір-біріне жақсы тілектер айтып, бата алған.",
            "options": [
                {"text": "Дұрыс", "is_correct": True},
                {"text": "Бұрыс", "is_correct": False},
            ]
        },
    ]
}


async def create_test(session: AsyncSession, test_data: dict) -> Test:
    """Create a test with questions and options."""
    # Check if test already exists
    result = await session.execute(
        select(Test).where(
            Test.title == test_data["title"],
            Test.chapter_id == test_data["chapter_id"],
            Test.is_deleted == False
        )
    )
    existing_test = result.scalar_one_or_none()

    if existing_test:
        print(f"  ⏭️  Тест уже существует: {test_data['title']}")
        return existing_test

    # Create test
    test = Test(
        title=test_data["title"],
        description=test_data["description"],
        textbook_id=TEXTBOOK_ID,
        chapter_id=test_data["chapter_id"],
        school_id=None,  # Global test
        test_purpose=TestPurpose.FORMATIVE,
        difficulty=DifficultyLevel.MEDIUM,
        time_limit=15,  # 15 minutes
        passing_score=0.7,
        is_active=True,
        is_deleted=False
    )
    session.add(test)
    await session.flush()

    # Create questions
    for idx, q_data in enumerate(test_data["questions"], start=1):
        question = Question(
            test_id=test.id,
            sort_order=idx,
            question_type=q_data["question_type"],
            question_text=q_data["question_text"],
            explanation=q_data["explanation"],
            points=1.0,
            is_deleted=False
        )
        session.add(question)
        await session.flush()

        # Create options
        for opt_idx, opt_data in enumerate(q_data["options"], start=1):
            option = QuestionOption(
                question_id=question.id,
                sort_order=opt_idx,
                option_text=opt_data["text"],
                is_correct=opt_data["is_correct"],
                is_deleted=False
            )
            session.add(option)

    await session.flush()
    print(f"  ✅ Создан тест: {test_data['title']} ({len(test_data['questions'])} вопросов)")
    return test


async def seed_tests():
    """Main function to seed tests."""
    print("=" * 60)
    print("🌱 Создание тестов по Қазақстан тарихы для 7 класса")
    print("=" * 60)
    print(f"📚 Textbook ID: {TEXTBOOK_ID}")
    print(f"📖 Chapter 1 ID: {CHAPTER_1_ID} (Қазақ-жоңғар соғыстары)")
    print(f"📖 Chapter 2 ID: {CHAPTER_2_ID} (XVIII ғасырдағы Қазақ хандығы)")
    print(f"📖 Chapter 3 ID: {CHAPTER_3_ID} (XVIII ғасырдағы Қазақстан мәдениеті)")
    print("=" * 60)
    print()

    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            # Create Test 1
            print("📝 Тест 1: Қазақ-жоңғар соғыстары")
            await create_test(session, TEST_1_DATA)

            # Create Test 2
            print("📝 Тест 2: Абылай хан дәуірі")
            await create_test(session, TEST_2_DATA)

            # Create Test 3
            print("📝 Тест 3: XVIII ғасырдағы мәдениет")
            await create_test(session, TEST_3_DATA)

            await session.commit()
            print()
            print("=" * 60)
            print("✅ Все тесты успешно созданы!")
            print("=" * 60)

        except Exception as e:
            await session.rollback()
            print(f"❌ Ошибка: {e}")
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_tests())
