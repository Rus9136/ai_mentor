/**
 * Test data generators and fixtures
 */

export function generateSchoolData() {
  const timestamp = Date.now();
  return {
    name: `Тестовая школа ${timestamp}`,
    code: `TEST${timestamp}`,
    region: 'Алматы',
    license_type: 'basic',
  };
}

export function generateTextbookData() {
  const timestamp = Date.now();
  return {
    title: `Тестовый учебник ${timestamp}`,
    subject: 'Математика',
    grade_level: 7,
    author: 'Автор Тестовый',
    publisher: 'Издательство Тест',
    year: 2024,
    language: 'ru',
  };
}

export function generateChapterData() {
  const timestamp = Date.now();
  return {
    chapter_number: '1',
    title: `Тестовая глава ${timestamp}`,
    order_index: 1,
  };
}

export function generateParagraphData() {
  const timestamp = Date.now();
  return {
    paragraph_number: '1.1',
    title: `Тестовый параграф ${timestamp}`,
    content: `Это содержимое тестового параграфа ${timestamp}`,
    order_index: 1,
  };
}

export function generateTestData() {
  const timestamp = Date.now();
  return {
    title: `Тестовый тест ${timestamp}`,
    duration_minutes: 30,
    passing_score: 70,
    difficulty_level: 2,
  };
}

export function generateQuestionData(type: string = 'SINGLE_CHOICE') {
  const timestamp = Date.now();
  return {
    question_type: type,
    question_text: `Вопрос ${timestamp}?`,
    points: 1,
    order_index: 1,
  };
}

export function generateStudentData() {
  const timestamp = Date.now();
  return {
    first_name: 'Тест',
    last_name: `Студентов${timestamp}`,
    email: `student${timestamp}@test.com`,
    password: 'test123',
    grade_level: 7,
  };
}

export function generateTeacherData() {
  const timestamp = Date.now();
  return {
    first_name: 'Тест',
    last_name: `Учителев${timestamp}`,
    email: `teacher${timestamp}@test.com`,
    password: 'test123',
  };
}

export function generateClassData() {
  const timestamp = Date.now();
  return {
    name: `7А-${timestamp}`,
    grade_level: 7,
    academic_year: '2024-2025',
  };
}

/**
 * Wait for specific duration
 */
export async function wait(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
