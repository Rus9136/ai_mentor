/**
 * Mock data for E2E tests
 */

export const mockUser = {
  id: 1,
  email: 'student@test.com',
  first_name: 'Test',
  last_name: 'Student',
  middle_name: null,
  role: 'student',
  school_id: 1,
  grade_level: 7,
  avatar_url: null,
  created_at: '2024-01-01T00:00:00Z',
};

export const mockTextbooks = [
  {
    id: 1,
    title: 'История Казахстана',
    subject: 'history',
    grade_level: 7,
    description: 'Учебник по истории Казахстана для 7 класса',
    is_global: true,
    progress: {
      chapters_total: 10,
      chapters_completed: 2,
      paragraphs_total: 50,
      paragraphs_completed: 8,
      percentage: 16,
    },
    mastery_level: 'B',
    last_activity: new Date().toISOString(),
    author: 'Министерство образования РК',
    chapters_count: 10,
  },
  {
    id: 2,
    title: 'Алгебра',
    subject: 'algebra',
    grade_level: 7,
    description: 'Учебник по алгебре для 7 класса',
    is_global: true,
    progress: {
      chapters_total: 8,
      chapters_completed: 0,
      paragraphs_total: 40,
      paragraphs_completed: 0,
      percentage: 0,
    },
    mastery_level: null,
    last_activity: null,
    author: 'Министерство образования РК',
    chapters_count: 8,
  },
];

export const mockChapters = [
  {
    id: 1,
    textbook_id: 1,
    title: 'Древний Казахстан',
    number: 1,
    order: 1,
    description: 'Изучение древней истории Казахстана',
    learning_objective: 'Понять историю древнего Казахстана',
    status: 'in_progress',
    progress: {
      paragraphs_total: 5,
      paragraphs_completed: 2,
      percentage: 40,
    },
    mastery_level: 'B',
    mastery_score: 75,
    has_summative_test: true,
    summative_passed: null,
  },
  {
    id: 2,
    textbook_id: 1,
    title: 'Средневековье',
    number: 2,
    order: 2,
    description: 'Средневековая история Казахстана',
    learning_objective: 'Изучить средневековую историю',
    status: 'not_started',
    progress: {
      paragraphs_total: 5,
      paragraphs_completed: 0,
      percentage: 0,
    },
    mastery_level: null,
    mastery_score: null,
    has_summative_test: true,
    summative_passed: null,
  },
];

export const mockParagraphs = [
  {
    id: 1,
    chapter_id: 1,
    title: 'Каменный век',
    number: 1,
    order: 1,
    summary: 'Краткое описание каменного века',
    learning_objective: 'Понять особенности каменного века',
    status: 'completed',
    estimated_time: 10,
    has_practice: true,
    practice_score: 0.85,
    key_terms: ['палеолит', 'неолит', 'мезолит'],
  },
  {
    id: 2,
    chapter_id: 1,
    title: 'Бронзовый век',
    number: 2,
    order: 2,
    summary: 'Краткое описание бронзового века',
    learning_objective: 'Изучить бронзовый век в Казахстане',
    status: 'in_progress',
    estimated_time: 12,
    has_practice: true,
    practice_score: null,
    key_terms: ['андроновская культура', 'бегазы-дандыбаевская'],
  },
  {
    id: 3,
    chapter_id: 1,
    title: 'Железный век',
    number: 3,
    order: 3,
    summary: 'Краткое описание железного века',
    learning_objective: 'Понять железный век',
    status: 'not_started',
    estimated_time: 15,
    has_practice: true,
    practice_score: null,
    key_terms: ['саки', 'скифы'],
  },
];

export const mockParagraph = {
  id: 2,
  chapter_id: 1,
  title: 'Бронзовый век',
  number: 2,
  order: 2,
  content: `<h2>Бронзовый век в Казахстане</h2>
<p>Бронзовый век на территории Казахстана охватывает период с конца III до начала I тысячелетия до н.э.</p>
<p>В это время происходит развитие металлургии, скотоводства и земледелия.</p>
<h3>Андроновская культура</h3>
<p>Наиболее известная культура бронзового века - андроновская культура, распространённая на территории современного Казахстана.</p>`,
  summary: 'Бронзовый век - важный период в истории Казахстана',
  learning_objective: 'Изучить особенности бронзового века в Казахстане',
  lesson_objective: null,
  key_terms: ['андроновская культура', 'бегазы-дандыбаевская', 'металлургия'],
  questions: null,
  status: 'in_progress',
  current_step: 'content',
  has_audio: true,
  has_video: false,
  has_slides: false,
  has_cards: true,
  chapter_title: 'Древний Казахстан',
  textbook_title: 'История Казахстана',
};

export const mockParagraphContent = {
  paragraph_id: 2,
  explain_text: `<h2>Бронзовый век в Казахстане</h2>
<p>Бронзовый век на территории Казахстана охватывает период с конца III до начала I тысячелетия до н.э.</p>
<p>В это время происходит развитие металлургии, скотоводства и земледелия.</p>`,
  audio_url: 'https://example.com/audio/bronze-age.mp3',
  video_url: null,
  slides_url: null,
  has_audio: true,
  has_cards: true,
  cards: [
    { id: '1', type: 'term', front: 'Андроновская культура', back: 'Археологическая культура эпохи бронзы', order: 1 },
    { id: '2', type: 'term', front: 'Бегазы-дандыбаевская культура', back: 'Культура позднего бронзового века', order: 2 },
    { id: '3', type: 'term', front: 'Металлургия', back: 'Обработка металлов', order: 3 },
  ],
};

export const mockParagraphNavigation = {
  current_paragraph_id: 2,
  current_paragraph_number: 2,
  chapter_id: 1,
  chapter_title: 'Древний Казахстан',
  textbook_id: 1,
  textbook_title: 'История Казахстана',
  previous_paragraph_id: 1,
  next_paragraph_id: 3,
  total_paragraphs_in_chapter: 5,
  current_position_in_chapter: 2,
};

export const mockParagraphProgress = {
  paragraph_id: 2,
  is_completed: false,
  current_step: 'content',
  time_spent: 120,
  last_accessed_at: new Date().toISOString(),
  completed_at: null,
  self_assessment: null,
  self_assessment_at: null,
  available_steps: ['content', 'practice', 'summary'],
  embedded_questions_total: 3,
  embedded_questions_answered: 0,
  embedded_questions_correct: 0,
};

export const mockParagraphProgressPractice = {
  ...mockParagraphProgress,
  current_step: 'practice',
  embedded_questions_answered: 1,
  embedded_questions_correct: 1,
};

export const mockParagraphProgressSummary = {
  ...mockParagraphProgress,
  current_step: 'summary',
  embedded_questions_answered: 3,
  embedded_questions_correct: 2,
};

export const mockParagraphProgressCompleted = {
  ...mockParagraphProgress,
  current_step: 'completed',
  is_completed: true,
  self_assessment: 'understood',
  self_assessment_at: new Date().toISOString(),
  completed_at: new Date().toISOString(),
  embedded_questions_answered: 3,
  embedded_questions_correct: 2,
};

export const mockEmbeddedQuestions = [
  {
    id: 1,
    paragraph_id: 2,
    question_text: 'Какая культура была наиболее распространена в бронзовом веке Казахстана?',
    question_type: 'single_choice',
    options: [
      { id: 'a', text: 'Андроновская культура' },
      { id: 'b', text: 'Ботайская культура' },
      { id: 'c', text: 'Афанасьевская культура' },
    ],
    hint: 'Эта культура названа по месту первых находок',
    sort_order: 1,
  },
  {
    id: 2,
    paragraph_id: 2,
    question_text: 'Выберите все характеристики бронзового века:',
    question_type: 'multiple_choice',
    options: [
      { id: 'a', text: 'Развитие металлургии' },
      { id: 'b', text: 'Появление письменности' },
      { id: 'c', text: 'Развитие скотоводства' },
      { id: 'd', text: 'Строительство пирамид' },
    ],
    hint: null,
    sort_order: 2,
  },
  {
    id: 3,
    paragraph_id: 2,
    question_text: 'Бронзовый век предшествовал железному веку?',
    question_type: 'true_false',
    options: null,
    hint: 'Подумайте о хронологии',
    sort_order: 3,
  },
];

export const mockAnswerCorrect = {
  is_correct: true,
  correct_answer: 'a',
  explanation: 'Андроновская культура - основная культура бронзового века в Казахстане',
  attempts_count: 1,
};

export const mockAnswerIncorrect = {
  is_correct: false,
  correct_answer: 'a',
  explanation: 'Правильный ответ: Андроновская культура. Она была наиболее распространена на территории Казахстана в эпоху бронзы.',
  attempts_count: 1,
};

export const mockSelfAssessmentResponse = {
  id: 1,
  paragraph_id: 2,
  rating: 'understood',
  practice_score: null,
  mastery_impact: 5.0,
  next_recommendation: 'next_paragraph',
  created_at: new Date().toISOString(),
};

export const mockStudentStats = {
  streak_days: 5,
  total_paragraphs_completed: 8,
  total_questions_answered: 24,
  total_time_spent: 3600,
  last_activity_date: new Date().toISOString(),
};

export const mockMasteryOverview = {
  textbooks: [
    {
      textbook_id: 1,
      textbook_title: 'История Казахстана',
      chapters: [
        {
          chapter_id: 1,
          chapter_title: 'Древний Казахстан',
          mastery_level: 'B',
          mastery_score: 75,
          paragraphs_completed: 2,
          paragraphs_total: 5,
        },
      ],
    },
  ],
};
