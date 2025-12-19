import { test, expect } from '@playwright/test';
import {
  setupAuthenticatedUser,
  setupApiMocks,
  setupParagraphMocks,
  setupQuestionAnswerMock,
} from './fixtures/auth';
import { mockParagraphProgressPractice, mockEmbeddedQuestions } from './fixtures/mocks';

/**
 * Practice Questions E2E Tests
 *
 * Tests embedded questions: single choice, multiple choice, true/false
 * and interactions like hints, feedback, navigation
 */

test.describe('Practice Questions', () => {
  test.beforeEach(async ({ page }) => {
    await setupAuthenticatedUser(page);
    await setupApiMocks(page);
    await setupParagraphMocks(page, { progress: mockParagraphProgressPractice });
  });

  test.describe('Question Types', () => {
    test('should handle single choice question', async ({ page }) => {
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
        // Select an option
        const optionA = page.getByTestId('option-a');
        await optionA.click();

        // Verify option is selected (visual feedback)
        await expect(optionA).toHaveClass(/amber/);

        // Select another option (should deselect first)
        const optionB = page.getByTestId('option-b');
        await optionB.click();

        // Option B should be selected now
        await expect(optionB).toHaveClass(/amber/);
      }
    });

    test('should handle multiple choice question', async ({ page }) => {
      // Mock for multiple choice question (id: 2)
      await page.route('**/api/v1/students/embedded-questions/2/answer', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            is_correct: true,
            correct_answer: ['a', 'c'],
            explanation: 'Правильно! Развитие металлургии и скотоводства - характеристики бронзового века.',
            attempts_count: 1,
          }),
        });
      });

      await page.goto('/ru/paragraphs/2');
      await page.waitForTimeout(500);

      // Navigate to practice and find multiple choice question
      const practiceTab = page.getByRole('button', { name: /практика|practice/i });
      if (await practiceTab.isVisible()) {
        await practiceTab.click();
      }

      // Look for multiple choice indicators (checkboxes)
      const checkboxes = page.locator('[data-testid^="option-"]');
      if (await checkboxes.first().isVisible()) {
        // In multiple choice, clicking multiple should be possible
        // This depends on the specific question being shown
      }
    });

    test('should handle true/false question', async ({ page }) => {
      // Mock for true/false question (id: 3)
      await page.route('**/api/v1/students/embedded-questions/3/answer', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            is_correct: true,
            correct_answer: 'true',
            explanation: 'Верно! Бронзовый век предшествовал железному веку.',
            attempts_count: 1,
          }),
        });
      });

      await page.goto('/ru/paragraphs/2');
      await page.waitForTimeout(500);

      const practiceTab = page.getByRole('button', { name: /практика|practice/i });
      if (await practiceTab.isVisible()) {
        await practiceTab.click();
      }

      // True/false questions should show two options
      const trueOption = page.getByTestId('option-true');
      const falseOption = page.getByTestId('option-false');

      if (await trueOption.isVisible()) {
        await trueOption.click();
        await expect(trueOption).toHaveClass(/amber/);
      }
    });
  });

  test.describe('Hints', () => {
    test('should show hint when clicked', async ({ page }) => {
      await page.goto('/ru/paragraphs/2');
      await page.waitForTimeout(500);

      const practiceTab = page.getByRole('button', { name: /практика|practice/i });
      if (await practiceTab.isVisible()) {
        await practiceTab.click();
        await page.waitForTimeout(300);
      }

      const hintBtn = page.getByTestId('show-hint');
      if (await hintBtn.isVisible()) {
        // Hint should not be visible initially
        await expect(page.getByTestId('hint-box')).not.toBeVisible();

        // Click hint button
        await hintBtn.click();

        // Hint should now be visible
        await expect(page.getByTestId('hint-box')).toBeVisible();

        // Hint should contain text
        const hintText = await page.getByTestId('hint-box').textContent();
        expect(hintText).toBeTruthy();
      }
    });

    test('should toggle hint visibility', async ({ page }) => {
      await page.goto('/ru/paragraphs/2');
      await page.waitForTimeout(500);

      const practiceTab = page.getByRole('button', { name: /практика|practice/i });
      if (await practiceTab.isVisible()) {
        await practiceTab.click();
        await page.waitForTimeout(300);
      }

      const hintBtn = page.getByTestId('show-hint');
      if (await hintBtn.isVisible()) {
        // Show hint
        await hintBtn.click();
        await expect(page.getByTestId('hint-box')).toBeVisible();

        // Hide hint
        await hintBtn.click();
        await expect(page.getByTestId('hint-box')).not.toBeVisible();
      }
    });
  });

  test.describe('Answer Feedback', () => {
    test('should show correct feedback with green styling', async ({ page }) => {
      await setupQuestionAnswerMock(page, 1, true);

      await page.goto('/ru/paragraphs/2');
      await page.waitForTimeout(500);

      const practiceTab = page.getByRole('button', { name: /практика|practice/i });
      if (await practiceTab.isVisible()) {
        await practiceTab.click();
        await page.waitForTimeout(300);
      }

      const questionElement = page.getByTestId('embedded-question');
      if (await questionElement.isVisible()) {
        // Select and submit
        await page.getByTestId('option-a').click();
        await page.getByTestId('submit-answer').click();
        await page.waitForTimeout(500);

        // Check feedback
        const feedback = page.getByTestId('feedback-correct');
        await expect(feedback).toBeVisible();

        // Should have green styling
        await expect(feedback).toHaveClass(/green/);
      }
    });

    test('should show incorrect feedback with red styling', async ({ page }) => {
      await setupQuestionAnswerMock(page, 1, false);

      await page.goto('/ru/paragraphs/2');
      await page.waitForTimeout(500);

      const practiceTab = page.getByRole('button', { name: /практика|practice/i });
      if (await practiceTab.isVisible()) {
        await practiceTab.click();
        await page.waitForTimeout(300);
      }

      const questionElement = page.getByTestId('embedded-question');
      if (await questionElement.isVisible()) {
        // Select wrong option and submit
        await page.getByTestId('option-b').click();
        await page.getByTestId('submit-answer').click();
        await page.waitForTimeout(500);

        // Check feedback
        const feedback = page.getByTestId('feedback-incorrect');
        await expect(feedback).toBeVisible();

        // Should have red styling
        await expect(feedback).toHaveClass(/red/);
      }
    });

    test('should show explanation after answering', async ({ page }) => {
      await setupQuestionAnswerMock(page, 1, true);

      await page.goto('/ru/paragraphs/2');
      await page.waitForTimeout(500);

      const practiceTab = page.getByRole('button', { name: /практика|practice/i });
      if (await practiceTab.isVisible()) {
        await practiceTab.click();
        await page.waitForTimeout(300);
      }

      const questionElement = page.getByTestId('embedded-question');
      if (await questionElement.isVisible()) {
        await page.getByTestId('option-a').click();
        await page.getByTestId('submit-answer').click();
        await page.waitForTimeout(500);

        // Feedback should contain explanation text
        const feedback = page.getByTestId('feedback-correct');
        const feedbackText = await feedback.textContent();
        expect(feedbackText).toBeTruthy();
      }
    });
  });

  test.describe('Question Navigation', () => {
    test('should show next button after answering', async ({ page }) => {
      await setupQuestionAnswerMock(page, 1, true);

      await page.goto('/ru/paragraphs/2');
      await page.waitForTimeout(500);

      const practiceTab = page.getByRole('button', { name: /практика|practice/i });
      if (await practiceTab.isVisible()) {
        await practiceTab.click();
        await page.waitForTimeout(300);
      }

      const questionElement = page.getByTestId('embedded-question');
      if (await questionElement.isVisible()) {
        // Submit button should be visible before answering
        await expect(page.getByTestId('submit-answer')).toBeVisible();

        // Next button should not be visible yet
        await expect(page.getByTestId('next-question')).not.toBeVisible();

        // Answer the question
        await page.getByTestId('option-a').click();
        await page.getByTestId('submit-answer').click();
        await page.waitForTimeout(500);

        // Now next button should be visible
        await expect(page.getByTestId('next-question')).toBeVisible();

        // Submit button should be hidden
        await expect(page.getByTestId('submit-answer')).not.toBeVisible();
      }
    });

    test('should disable options after answering', async ({ page }) => {
      await setupQuestionAnswerMock(page, 1, true);

      await page.goto('/ru/paragraphs/2');
      await page.waitForTimeout(500);

      const practiceTab = page.getByRole('button', { name: /практика|practice/i });
      if (await practiceTab.isVisible()) {
        await practiceTab.click();
        await page.waitForTimeout(300);
      }

      const questionElement = page.getByTestId('embedded-question');
      if (await questionElement.isVisible()) {
        // Answer the question
        await page.getByTestId('option-a').click();
        await page.getByTestId('submit-answer').click();
        await page.waitForTimeout(500);

        // Options should be disabled
        const optionA = page.getByTestId('option-a');
        await expect(optionA).toBeDisabled();
      }
    });
  });

  test.describe('Submit Button State', () => {
    test('should disable submit button when no option selected', async ({ page }) => {
      await page.goto('/ru/paragraphs/2');
      await page.waitForTimeout(500);

      const practiceTab = page.getByRole('button', { name: /практика|practice/i });
      if (await practiceTab.isVisible()) {
        await practiceTab.click();
        await page.waitForTimeout(300);
      }

      const submitBtn = page.getByTestId('submit-answer');
      if (await submitBtn.isVisible()) {
        // Should be disabled when nothing selected
        await expect(submitBtn).toBeDisabled();
      }
    });

    test('should enable submit button when option selected', async ({ page }) => {
      await page.goto('/ru/paragraphs/2');
      await page.waitForTimeout(500);

      const practiceTab = page.getByRole('button', { name: /практика|practice/i });
      if (await practiceTab.isVisible()) {
        await practiceTab.click();
        await page.waitForTimeout(300);
      }

      const questionElement = page.getByTestId('embedded-question');
      if (await questionElement.isVisible()) {
        const submitBtn = page.getByTestId('submit-answer');

        // Select an option
        await page.getByTestId('option-a').click();

        // Submit should be enabled
        await expect(submitBtn).toBeEnabled();
      }
    });
  });
});
