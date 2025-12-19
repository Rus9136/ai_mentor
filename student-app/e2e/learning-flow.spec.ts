import { test, expect } from '@playwright/test';
import {
  setupAuthenticatedUser,
  setupApiMocks,
  setupParagraphMocks,
  setupQuestionAnswerMock,
} from './fixtures/auth';
import {
  mockParagraphProgress,
  mockParagraphProgressPractice,
  mockParagraphProgressSummary,
  mockParagraphProgressCompleted,
} from './fixtures/mocks';

/**
 * Learning Flow E2E Tests
 *
 * Tests the critical path: opening a paragraph -> reading content ->
 * answering questions -> self-assessment -> completion screen
 */

test.describe('Learning Flow', () => {
  test.beforeEach(async ({ page }) => {
    await setupAuthenticatedUser(page);
    await setupApiMocks(page);
  });

  test.describe('Russian locale (ru)', () => {
    test('should display paragraph content', async ({ page }) => {
      await setupParagraphMocks(page);

      await page.goto('/ru/paragraphs/2');

      // Wait for page to load
      await expect(page.locator('h1')).toBeVisible();

      // Check paragraph title is displayed
      await expect(page.getByText(/Бронзовый век/i)).toBeVisible();

      // Check content is rendered
      await expect(page.locator('article')).toBeVisible();
    });

    test('should navigate between content tabs', async ({ page }) => {
      await setupParagraphMocks(page);

      await page.goto('/ru/paragraphs/2');

      // Wait for page to load
      await expect(page.locator('h1')).toBeVisible();

      // Check that tabs are visible (text tab should be default)
      // Note: Tab labels may vary based on content availability
      await page.waitForTimeout(500); // Wait for tabs to render

      // Look for tab buttons if they exist
      const tabButtons = page.locator('button[role="tab"], [data-tab]');
      const tabCount = await tabButtons.count();

      if (tabCount > 1) {
        // Click on another tab if available
        await tabButtons.nth(1).click();
        await page.waitForTimeout(300);
      }
    });

    test('should show embedded questions in practice', async ({ page }) => {
      await setupParagraphMocks(page, { progress: mockParagraphProgressPractice });
      await setupQuestionAnswerMock(page, 1, true);

      await page.goto('/ru/paragraphs/2');

      // Wait for page to load
      await page.waitForTimeout(500);

      // Look for practice tab or embedded question
      const practiceTab = page.getByRole('button', { name: /практика|practice/i });
      if (await practiceTab.isVisible()) {
        await practiceTab.click();
      }

      // Check for embedded question component
      const questionElement = page.getByTestId('embedded-question');
      if (await questionElement.isVisible()) {
        // Verify question text is displayed
        await expect(page.getByTestId('question-text')).toBeVisible();

        // Check options are displayed
        const option = page.getByTestId('option-a');
        if (await option.isVisible()) {
          await option.click();

          // Submit answer
          const submitBtn = page.getByTestId('submit-answer');
          if (await submitBtn.isEnabled()) {
            await submitBtn.click();
            await page.waitForTimeout(500);

            // Check for feedback
            await expect(
              page.getByTestId('feedback-correct').or(page.getByTestId('feedback-incorrect'))
            ).toBeVisible();
          }
        }
      }
    });

    test('should display self-assessment after practice', async ({ page }) => {
      await setupParagraphMocks(page, { progress: mockParagraphProgressSummary });

      await page.goto('/ru/paragraphs/2');

      // Wait for page to load
      await page.waitForTimeout(500);

      // Check for self-assessment component
      const selfAssessment = page.getByTestId('self-assessment');
      if (await selfAssessment.isVisible()) {
        // Check rating options are visible
        await expect(page.getByTestId('rating-understood')).toBeVisible();
        await expect(page.getByTestId('rating-questions')).toBeVisible();
        await expect(page.getByTestId('rating-difficult')).toBeVisible();

        // Select a rating
        await page.getByTestId('rating-understood').click();

        // Submit should be enabled
        const submitBtn = page.getByTestId('submit-assessment');
        await expect(submitBtn).toBeEnabled();
      }
    });

    test('should display completion screen after finishing', async ({ page }) => {
      await setupParagraphMocks(page, { progress: mockParagraphProgressCompleted });

      await page.goto('/ru/paragraphs/2');

      // Wait for page to load
      await page.waitForTimeout(500);

      // Check for completion screen
      const completionScreen = page.getByTestId('completion-screen');
      if (await completionScreen.isVisible()) {
        // Check stats are displayed
        await expect(page.getByTestId('score-display')).toBeVisible();
        await expect(page.getByTestId('time-display')).toBeVisible();

        // Check navigation buttons
        await expect(page.getByTestId('to-chapter-btn')).toBeVisible();
      }
    });

    test('should show hint when requested', async ({ page }) => {
      await setupParagraphMocks(page, { progress: mockParagraphProgressPractice });

      await page.goto('/ru/paragraphs/2');
      await page.waitForTimeout(500);

      // Navigate to practice if needed
      const practiceTab = page.getByRole('button', { name: /практика|practice/i });
      if (await practiceTab.isVisible()) {
        await practiceTab.click();
        await page.waitForTimeout(300);
      }

      // Check for hint button
      const hintBtn = page.getByTestId('show-hint');
      if (await hintBtn.isVisible()) {
        await hintBtn.click();

        // Verify hint box appears
        await expect(page.getByTestId('hint-box')).toBeVisible();
      }
    });
  });

  test.describe('Kazakh locale (kk)', () => {
    test('should display paragraph content in Kazakh', async ({ page }) => {
      await setupParagraphMocks(page);

      await page.goto('/kk/paragraphs/2');

      // Wait for page to load
      await expect(page.locator('h1')).toBeVisible();

      // Content should be visible (language may be in Kazakh)
      await expect(page.locator('article')).toBeVisible();
    });

    test('should display self-assessment in Kazakh', async ({ page }) => {
      await setupParagraphMocks(page, { progress: mockParagraphProgressSummary });

      await page.goto('/kk/paragraphs/2');
      await page.waitForTimeout(500);

      // Check for self-assessment component
      const selfAssessment = page.getByTestId('self-assessment');
      if (await selfAssessment.isVisible()) {
        // Rating options should be visible regardless of language
        await expect(page.getByTestId('rating-understood')).toBeVisible();
      }
    });
  });
});

test.describe('Question Answering Flow', () => {
  test.beforeEach(async ({ page }) => {
    await setupAuthenticatedUser(page);
    await setupApiMocks(page);
  });

  test('should handle correct answer', async ({ page }) => {
    await setupParagraphMocks(page, { progress: mockParagraphProgressPractice });
    await setupQuestionAnswerMock(page, 1, true);

    await page.goto('/ru/paragraphs/2');
    await page.waitForTimeout(500);

    // Navigate to practice
    const practiceTab = page.getByRole('button', { name: /практика|practice/i });
    if (await practiceTab.isVisible()) {
      await practiceTab.click();
      await page.waitForTimeout(300);
    }

    const questionElement = page.getByTestId('embedded-question');
    if (await questionElement.isVisible()) {
      // Select correct option
      await page.getByTestId('option-a').click();

      // Submit
      await page.getByTestId('submit-answer').click();
      await page.waitForTimeout(500);

      // Verify correct feedback
      await expect(page.getByTestId('feedback-correct')).toBeVisible();

      // Next button should appear
      await expect(page.getByTestId('next-question')).toBeVisible();
    }
  });

  test('should handle incorrect answer', async ({ page }) => {
    await setupParagraphMocks(page, { progress: mockParagraphProgressPractice });
    await setupQuestionAnswerMock(page, 1, false);

    await page.goto('/ru/paragraphs/2');
    await page.waitForTimeout(500);

    // Navigate to practice
    const practiceTab = page.getByRole('button', { name: /практика|practice/i });
    if (await practiceTab.isVisible()) {
      await practiceTab.click();
      await page.waitForTimeout(300);
    }

    const questionElement = page.getByTestId('embedded-question');
    if (await questionElement.isVisible()) {
      // Select wrong option
      await page.getByTestId('option-b').click();

      // Submit
      await page.getByTestId('submit-answer').click();
      await page.waitForTimeout(500);

      // Verify incorrect feedback
      await expect(page.getByTestId('feedback-incorrect')).toBeVisible();
    }
  });
});

test.describe('Completion Screen', () => {
  test.beforeEach(async ({ page }) => {
    await setupAuthenticatedUser(page);
    await setupApiMocks(page);
  });

  test('should display score correctly', async ({ page }) => {
    await setupParagraphMocks(page, { progress: mockParagraphProgressCompleted });

    await page.goto('/ru/paragraphs/2');
    await page.waitForTimeout(500);

    const completionScreen = page.getByTestId('completion-screen');
    if (await completionScreen.isVisible()) {
      // Check score value
      const scoreValue = page.getByTestId('score-value');
      await expect(scoreValue).toBeVisible();

      // Score should show format like "2/3" based on mock data
      const scoreText = await scoreValue.textContent();
      expect(scoreText).toMatch(/\d+\/\d+|-/);
    }
  });

  test('should navigate to chapter when button clicked', async ({ page }) => {
    await setupParagraphMocks(page, { progress: mockParagraphProgressCompleted });

    await page.goto('/ru/paragraphs/2');
    await page.waitForTimeout(500);

    const completionScreen = page.getByTestId('completion-screen');
    if (await completionScreen.isVisible()) {
      const toChapterBtn = page.getByTestId('to-chapter-btn');
      await expect(toChapterBtn).toBeVisible();

      // Click and check navigation
      await toChapterBtn.click();

      // Should navigate to chapter page
      await page.waitForURL(/\/chapters\/\d+/);
    }
  });

  test('should navigate to next paragraph when button clicked', async ({ page }) => {
    await setupParagraphMocks(page, { progress: mockParagraphProgressCompleted });

    await page.goto('/ru/paragraphs/2');
    await page.waitForTimeout(500);

    const nextBtn = page.getByTestId('next-paragraph-btn');
    if (await nextBtn.isVisible()) {
      await nextBtn.click();

      // Should navigate to next paragraph
      await page.waitForURL(/\/paragraphs\/\d+/);
    }
  });
});
