"""
Generate comprehensive grades SQL for all students.
Profiles consistent with mastery data from seed_test_data.sql.
"""

import random
from datetime import date, timedelta

random.seed(42)

# ============================================================================
# CONFIG
# ============================================================================

SCHOOL_ID = 5
ACADEMIC_YEAR = "2025-2026"

# Subjects for grade 7 (class 7-A, class_id=1)
SUBJECTS_7 = [
    (24, "Алгебра"),
    (25, "Геометрия"),
    (1,  "История Казахстана"),
    (26, "Физика"),
    (32, "Казахский язык"),
    (33, "Русский язык"),
    (34, "Английский язык"),
    (31, "Информатика"),
]

# Subjects for grade 8 (class 8-Б, class_id=2)
SUBJECTS_8 = [
    (24, "Алгебра"),
    (25, "Геометрия"),
    (1,  "История Казахстана"),
    (26, "Физика"),
    (27, "Химия"),
    (32, "Казахский язык"),
    (33, "Русский язык"),
    (34, "Английский язык"),
]

# Teachers: (teacher_id, user_id, subject_ids they can grade)
# For subjects without a matching teacher, teacher_id=NULL, created_by=8
TEACHER_MAP = {
    # subject_id -> (teacher_id, user_id/created_by)
    24: (1, 8),   # Алгебра -> Айгуль (math)
    25: (1, 8),   # Геометрия -> Айгуль
    23: (1, 8),   # Математика -> Айгуль
    1:  (3, 22),  # История -> Алия
    26: (2, 9),   # Физика -> Ерлан
}
DEFAULT_TEACHER = (None, 8)  # teacher_id=NULL, created_by=Айгуль

# Quarter dates
Q1_CURRENT_DATES = [
    date(2025, 9, 10), date(2025, 9, 18), date(2025, 9, 25),
    date(2025, 10, 3), date(2025, 10, 10), date(2025, 10, 16),
]
Q1_SOR_DATE = date(2025, 10, 20)
Q1_SOCH_DATE = date(2025, 10, 25)

Q2_CURRENT_DATES = [
    date(2025, 11, 12), date(2025, 11, 25), date(2025, 12, 5),
    date(2025, 12, 15), date(2025, 12, 22),
]
Q2_SOR_DATE = date(2025, 12, 24)
Q2_SOCH_DATE = date(2025, 12, 27)

Q3_CURRENT_DATES = [
    date(2026, 1, 12), date(2026, 1, 22), date(2026, 2, 5),
    date(2026, 2, 15), date(2026, 2, 25),
]
Q3_SOR_DATE = date(2026, 2, 28)
# No SOCH yet for Q3 — quarter in progress

# ============================================================================
# STUDENT PROFILES
# grade_profile: {subject_id: (min_grade, max_grade, variance)}
# variance: how much grades fluctuate within range
# ============================================================================

# Class 7-A (class_id=1)
STUDENTS_7A = {
    # Student 5 (Алихан) — Отличник: strong across the board
    5: {
        "base": (9, 10),
        "subjects": {
            24: (9, 10),  # Алгебра — top
            25: (8, 10),  # Геометрия — strong
            1:  (9, 10),  # История — top
            26: (8, 10),  # Физика — strong
            32: (8, 10),  # Каз.язык — strong
            33: (9, 10),  # Рус.язык — top
            34: (8, 9),   # Англ.язык — good
            31: (9, 10),  # Информатика — top
        },
    },
    # Student 6 (Аружан) — Хорошистка: good overall, strong in languages
    6: {
        "base": (7, 9),
        "subjects": {
            24: (7, 8),   # Алгебра — ok
            25: (6, 8),   # Геометрия — weaker
            1:  (7, 9),   # История — good
            26: (6, 8),   # Физика — ok
            32: (8, 10),  # Каз.язык — strong
            33: (8, 9),   # Рус.язык — strong
            34: (8, 10),  # Англ.язык — strong
            31: (7, 8),   # Информатика — ok
        },
    },
    # Student 7 (Нурислам) — Средний: average, better in exact sciences
    7: {
        "base": (5, 7),
        "subjects": {
            24: (6, 8),   # Алгебра — stronger
            25: (6, 7),   # Геометрия — ok
            1:  (5, 7),   # История — average
            26: (6, 8),   # Физика — ok
            32: (4, 6),   # Каз.язык — weak
            33: (5, 7),   # Рус.язык — average
            34: (5, 6),   # Англ.язык — weak
            31: (7, 9),   # Информатика — good!
        },
    },
    # Student 8 (Жанель) — Отстающая: struggles everywhere
    8: {
        "base": (3, 5),
        "subjects": {
            24: (3, 5),   # Алгебра — weak
            25: (3, 4),   # Геометрия — very weak
            1:  (3, 5),   # История — weak
            26: (3, 5),   # Физика — weak
            32: (4, 6),   # Каз.язык — slightly better
            33: (4, 6),   # Рус.язык — slightly better
            34: (3, 5),   # Англ.язык — weak
            31: (4, 5),   # Информатика — weak
        },
    },
    # Student 9 (Данияр) — Неровный: wild variation between subjects and days
    9: {
        "base": (4, 9),
        "subjects": {
            24: (5, 9),   # Алгебра — varies wildly
            25: (4, 8),   # Геометрия — varies
            1:  (5, 8),   # История — varies
            26: (6, 9),   # Физика — can be good
            32: (4, 7),   # Каз.язык — varies
            33: (5, 8),   # Рус.язык — varies
            34: (4, 7),   # Англ.язык — varies
            31: (7, 10),  # Информатика — actually good
        },
    },
    # Student 10 (Айым) — Пассивная: low activity, occasional OK grades
    10: {
        "base": (4, 6),
        "subjects": {
            24: (4, 6),   # Алгебра — low
            25: (3, 5),   # Геометрия — low
            1:  (4, 5),   # История — low
            26: (4, 6),   # Физика — low
            32: (5, 7),   # Каз.язык — slightly better
            33: (5, 6),   # Рус.язык — ok
            34: (4, 6),   # Англ.язык — low
            31: (4, 6),   # Информатика — low
        },
    },
    # Student 17 (Рыскелдi) — Продвинутый (grade 11, but in 7-A class)
    17: {
        "base": (8, 10),
        "subjects": {
            24: (9, 10),  # Алгебра — excellent
            25: (8, 10),  # Геометрия — strong
            1:  (9, 10),  # История — excellent
            26: (9, 10),  # Физика — excellent
            32: (8, 9),   # Каз.язык — good
            33: (8, 10),  # Рус.язык — strong
            34: (7, 9),   # Англ.язык — good
            31: (9, 10),  # Информатика — excellent
        },
    },
}

# Class 8-Б (class_id=2)
STUDENTS_8B = {
    # Student 11 (Ернар) — Средний
    11: {
        "base": (5, 7),
        "subjects": {
            24: (5, 7), 25: (5, 7), 1: (6, 7), 26: (6, 8),
            27: (5, 7), 32: (5, 7), 33: (6, 7), 34: (5, 6),
        },
    },
    # Student 12 (Камила) — Отличница
    12: {
        "base": (8, 10),
        "subjects": {
            24: (8, 10), 25: (8, 9), 1: (9, 10), 26: (8, 10),
            27: (8, 10), 32: (9, 10), 33: (9, 10), 34: (8, 10),
        },
    },
    # Student 13 (Асхат) — Отстающий
    13: {
        "base": (3, 5),
        "subjects": {
            24: (3, 5), 25: (2, 4), 1: (3, 5), 26: (3, 5),
            27: (3, 4), 32: (4, 5), 33: (4, 5), 34: (3, 4),
        },
    },
    # Student 14 (Диана) — Прогрессирует (Q2 grades better than Q1)
    14: {
        "base": (6, 8),
        "subjects": {
            24: (6, 8), 25: (5, 7), 1: (6, 8), 26: (5, 7),
            27: (5, 7), 32: (7, 8), 33: (7, 9), 34: (6, 8),
        },
        "q2_bonus": 1,  # Q2 grades are 1 point higher
    },
    # Student 15 (Темирлан) — Не активный
    15: {
        "base": (4, 6),
        "subjects": {
            24: (4, 6), 25: (4, 5), 1: (4, 6), 26: (4, 6),
            27: (4, 5), 32: (4, 6), 33: (5, 6), 34: (4, 5),
        },
    },
    # Student 16 (Амина) — Стабильная
    16: {
        "base": (6, 8),
        "subjects": {
            24: (6, 7), 25: (6, 7), 1: (6, 8), 26: (6, 7),
            27: (6, 7), 32: (7, 8), 33: (7, 8), 34: (6, 8),
        },
    },
}


# ============================================================================
# GENERATE GRADES
# ============================================================================

def random_grade(lo, hi):
    """Generate a grade within range with slight bias toward center."""
    return random.randint(lo, hi)


def random_comment(grade_type, grade_value):
    """Occasionally add a comment."""
    if random.random() > 0.15:  # 85% no comment
        return None

    if grade_type == "SOCH":
        if grade_value >= 8:
            return random.choice([
                "Отличная работа за четверть",
                "Стабильно высокие результаты",
                "Молодец!",
            ])
        elif grade_value <= 4:
            return random.choice([
                "Нужно подтянуть",
                "Слабый результат за четверть",
                "Рекомендуется дополнительная подготовка",
            ])
    elif grade_type == "SOR":
        if grade_value >= 8:
            return random.choice(["Хорошо подготовился", "Отличный СОР"])
        elif grade_value <= 4:
            return random.choice(["Слабая подготовка к СОР", "Нужно заниматься"])
    else:
        if grade_value >= 9:
            return random.choice([
                "Отлично!", "Молодец!", "Активно работает",
                "Хорошая подготовка",
            ])
        elif grade_value <= 3:
            return random.choice([
                "Не готов к уроку", "Пропустил тему",
                "Нужно больше заниматься", "Слабая подготовка",
            ])
    return None


def generate_grades_for_student(
    student_id, class_id, subjects, profile, quarters
):
    """Generate all grades for a student."""
    grades = []

    for subj_id, subj_name in subjects:
        lo, hi = profile["subjects"].get(subj_id, profile["base"])
        q2_bonus = profile.get("q2_bonus", 0)
        teacher_id, created_by = TEACHER_MAP.get(subj_id, DEFAULT_TEACHER)

        for quarter, dates_cfg in quarters.items():
            current_dates = dates_cfg["current"]
            sor_date = dates_cfg["sor"]
            soch_date = dates_cfg.get("soch")

            # Apply Q2 bonus for students who improve
            q_lo = lo
            q_hi = hi
            if quarter >= 2 and q2_bonus:
                q_lo = min(lo + q2_bonus, 10)
                q_hi = min(hi + q2_bonus, 10)

            # Pick 4-5 random current dates
            n_current = random.randint(4, min(5, len(current_dates)))
            selected_dates = sorted(random.sample(current_dates, n_current))

            # CURRENT grades
            for d in selected_dates:
                val = random_grade(q_lo, q_hi)
                comment = random_comment("CURRENT", val)
                grades.append((
                    student_id, SCHOOL_ID, subj_id, class_id,
                    teacher_id, created_by, val, "CURRENT",
                    d, quarter, ACADEMIC_YEAR, comment
                ))

            # SOR grade (usually close to average of CURRENT)
            sor_val = random_grade(q_lo, q_hi)
            sor_comment = random_comment("SOR", sor_val)
            grades.append((
                student_id, SCHOOL_ID, subj_id, class_id,
                teacher_id, created_by, sor_val, "SOR",
                sor_date, quarter, ACADEMIC_YEAR, sor_comment
            ))

            # SOCH (only for completed quarters)
            if soch_date:
                # SOCH is usually weighted average, slightly rounded
                avg = sum(g[6] for g in grades
                          if g[0] == student_id and g[2] == subj_id
                          and g[9] == quarter) / (n_current + 1)
                soch_val = max(1, min(10, round(avg)))
                soch_comment = random_comment("SOCH", soch_val)
                grades.append((
                    student_id, SCHOOL_ID, subj_id, class_id,
                    teacher_id, created_by, soch_val, "SOCH",
                    soch_date, quarter, ACADEMIC_YEAR, soch_comment
                ))

    return grades


def main():
    quarters_q1_q2 = {
        1: {
            "current": Q1_CURRENT_DATES,
            "sor": Q1_SOR_DATE,
            "soch": Q1_SOCH_DATE,
        },
        2: {
            "current": Q2_CURRENT_DATES,
            "sor": Q2_SOR_DATE,
            "soch": Q2_SOCH_DATE,
        },
        3: {
            "current": Q3_CURRENT_DATES,
            "sor": Q3_SOR_DATE,
            # no soch — quarter in progress
        },
    }

    all_grades = []

    # Class 7-A
    for student_id, profile in STUDENTS_7A.items():
        all_grades.extend(
            generate_grades_for_student(
                student_id, 1, SUBJECTS_7, profile, quarters_q1_q2
            )
        )

    # Class 8-Б
    for student_id, profile in STUDENTS_8B.items():
        all_grades.extend(
            generate_grades_for_student(
                student_id, 2, SUBJECTS_8, profile, quarters_q1_q2
            )
        )

    # Generate SQL
    print("-- ============================================================================")
    print("-- Generated grades for Teacher Dashboard test data")
    print(f"-- Total: {len(all_grades)} grades")
    print("-- ============================================================================")
    print()
    print("BEGIN;")
    print()
    print("-- Clean existing grades")
    print("DELETE FROM grades WHERE student_id IN (5,6,7,8,9,10,11,12,13,14,15,16,17);")
    print()
    print("-- Insert grades")
    print("INSERT INTO grades (student_id, school_id, subject_id, class_id, teacher_id, created_by, grade_value, grade_type, grade_date, quarter, academic_year, comment) VALUES")

    lines = []
    for g in all_grades:
        (student_id, school_id, subj_id, class_id,
         teacher_id, created_by, val, gtype,
         gdate, quarter, academic_year, comment) = g

        tid = str(teacher_id) if teacher_id else "NULL"
        cmt = f"'{comment}'" if comment else "NULL"
        line = (
            f"({student_id}, {school_id}, {subj_id}, {class_id}, "
            f"{tid}, {created_by}, {val}, '{gtype}', "
            f"'{gdate}', {quarter}, '{academic_year}', {cmt})"
        )
        lines.append(line)

    print(",\n".join(lines) + ";")
    print()
    print("COMMIT;")
    print()
    print(f"-- Total grades: {len(all_grades)}")


if __name__ == "__main__":
    main()
