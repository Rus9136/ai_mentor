import { test as base, Page, Route } from '@playwright/test';
import {
  mockUser,
  mockTextbooks,
  mockChapters,
  mockParagraphs,
  mockParagraph,
  mockParagraphContent,
  mockParagraphNavigation,
  mockParagraphProgress,
  mockEmbeddedQuestions,
  mockStudentStats,
  mockMasteryOverview,
} from './mocks';

/**
 * Setup authenticated user by setting JWT tokens in localStorage
 */
export async function setupAuthenticatedUser(page: Page) {
  await page.addInitScript(() => {
    localStorage.setItem('ai_mentor_access_token', 'test_access_token_12345');
    localStorage.setItem('ai_mentor_refresh_token', 'test_refresh_token_12345');
  });
}

/**
 * Setup all API mocks for authenticated user
 */
export async function setupApiMocks(page: Page) {
  const API_BASE = '**/api/v1';

  // Auth: GET /auth/me
  await page.route(`${API_BASE}/auth/me`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(mockUser),
    });
  });

  // Auth: POST /auth/refresh
  await page.route(`${API_BASE}/auth/refresh`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        access_token: 'new_access_token',
        refresh_token: 'new_refresh_token',
        token_type: 'bearer',
      }),
    });
  });

  // Textbooks: GET /students/textbooks
  await page.route(`${API_BASE}/students/textbooks`, async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockTextbooks),
      });
    } else {
      await route.continue();
    }
  });

  // Chapters: GET /students/textbooks/{id}/chapters
  await page.route(`${API_BASE}/students/textbooks/*/chapters`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(mockChapters),
    });
  });

  // Paragraphs: GET /students/chapters/{id}/paragraphs
  await page.route(`${API_BASE}/students/chapters/*/paragraphs`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(mockParagraphs),
    });
  });

  // Stats: GET /students/stats
  await page.route(`${API_BASE}/students/stats`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(mockStudentStats),
    });
  });

  // Mastery: GET /students/mastery/overview
  await page.route(`${API_BASE}/students/mastery/overview`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(mockMasteryOverview),
    });
  });
}

/**
 * Setup paragraph-specific API mocks
 */
export async function setupParagraphMocks(
  page: Page,
  options: {
    paragraphId?: number;
    progress?: typeof mockParagraphProgress;
  } = {}
) {
  const API_BASE = '**/api/v1';
  const paragraphId = options.paragraphId || 2;
  const progress = options.progress || mockParagraphProgress;

  // Paragraph detail: GET /students/paragraphs/{id}
  await page.route(`${API_BASE}/students/paragraphs/${paragraphId}`, async (route) => {
    const url = route.request().url();

    // Skip if it's a sub-route like /progress, /content, etc.
    if (url.includes('/content') || url.includes('/progress') ||
        url.includes('/navigation') || url.includes('/embedded-questions') ||
        url.includes('/self-assessment')) {
      await route.continue();
      return;
    }

    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(mockParagraph),
    });
  });

  // Paragraph content: GET /students/paragraphs/{id}/content
  await page.route(`${API_BASE}/students/paragraphs/${paragraphId}/content*`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(mockParagraphContent),
    });
  });

  // Paragraph navigation: GET /students/paragraphs/{id}/navigation
  await page.route(`${API_BASE}/students/paragraphs/${paragraphId}/navigation`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(mockParagraphNavigation),
    });
  });

  // Paragraph progress: GET/POST /students/paragraphs/{id}/progress
  await page.route(`${API_BASE}/students/paragraphs/${paragraphId}/progress`, async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(progress),
      });
    } else if (route.request().method() === 'POST') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ ...progress, message: 'Progress updated' }),
      });
    } else {
      await route.continue();
    }
  });

  // Embedded questions: GET /students/paragraphs/{id}/embedded-questions
  await page.route(`${API_BASE}/students/paragraphs/${paragraphId}/embedded-questions`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(mockEmbeddedQuestions),
    });
  });

  // Self-assessment: POST /students/paragraphs/{id}/self-assessment
  await page.route(`${API_BASE}/students/paragraphs/${paragraphId}/self-assessment`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        paragraph_id: paragraphId,
        rating: 'understood',
        recorded_at: new Date().toISOString(),
        message: 'Assessment saved',
      }),
    });
  });
}

/**
 * Setup question answer mock
 */
export async function setupQuestionAnswerMock(
  page: Page,
  questionId: number,
  isCorrect: boolean = true
) {
  const API_BASE = '**/api/v1';

  await page.route(`${API_BASE}/students/embedded-questions/${questionId}/answer`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        is_correct: isCorrect,
        correct_answer: isCorrect ? 'a' : 'b',
        explanation: isCorrect
          ? 'Правильно! Отличная работа.'
          : 'Неправильно. Правильный ответ: Андроновская культура.',
        attempts_count: 1,
      }),
    });
  });
}

/**
 * Extended test with authenticated user fixture
 */
export const authenticatedTest = base.extend<{ authenticatedPage: Page }>({
  authenticatedPage: async ({ page }, use) => {
    await setupAuthenticatedUser(page);
    await setupApiMocks(page);
    await use(page);
  },
});

/**
 * Test with full paragraph mocks
 */
export const paragraphTest = base.extend<{ paragraphPage: Page }>({
  paragraphPage: async ({ page }, use) => {
    await setupAuthenticatedUser(page);
    await setupApiMocks(page);
    await setupParagraphMocks(page);
    await use(page);
  },
});

export { base as test };
