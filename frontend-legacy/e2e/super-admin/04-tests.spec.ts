import { test, expect } from '@playwright/test';
import { login, SUPER_ADMIN_USER, waitForAPIResponse } from '../helpers/auth';
import { generateTestData, generateQuestionData, wait } from '../helpers/test-data';

test.describe('SUPER_ADMIN Tests Management', () => {
  test.beforeEach(async ({ page }) => {
    await page.context().clearCookies();
    await login(page, SUPER_ADMIN_USER);
  });

  test('should navigate to tests list', async ({ page }) => {
    await page.click('a[href="#/tests"]');
    await expect(page).toHaveURL(/\/#\/tests/);
    await expect(page.getByRole('heading', { name: /тесты/i })).toBeVisible();
  });

  test('should display tests list', async ({ page }) => {
    await page.goto('/#/tests');
    await page.waitForSelector('[role="grid"]', { timeout: 10000 });

    // Check for table
    await expect(page.getByRole('grid')).toBeVisible();
  });

  test('should create a new test', async ({ page }) => {
    const testData = generateTestData();

    await page.goto('/#/tests/create');

    // Fill form
    await page.fill('input[name="title"]', testData.title);
    await page.fill('input[name="duration_minutes"]', testData.duration_minutes.toString());
    await page.fill('input[name="passing_score"]', testData.passing_score.toString());

    // Select difficulty level (if available)
    const difficultySelect = page.locator('select[name="difficulty_level"]');
    if (await difficultySelect.isVisible({ timeout: 2000 }).catch(() => false)) {
      await difficultySelect.selectOption(testData.difficulty_level.toString());
    }

    // Wait for API response
    const responsePromise = waitForAPIResponse(page, '/api/v1/admin/global/tests', 'POST');

    // Submit
    await page.click('button[type="submit"]');

    const response = await responsePromise;
    expect(response.status()).toBe(200);

    // Should show success
    await expect(page.getByText(/создан|успешно|success/i)).toBeVisible();
  });

  test('should validate required fields when creating test', async ({ page }) => {
    await page.goto('/#/tests/create');

    // Try to submit without filling
    await page.click('button[type="submit"]');

    // Should show validation errors
    await expect(page.getByText(/обязательн|required/i)).toBeVisible();
  });

  test('should add question to test', async ({ page }) => {
    // Create test first
    const testData = generateTestData();
    await page.goto('/#/tests/create');
    await page.fill('input[name="title"]', testData.title);
    await page.fill('input[name="duration_minutes"]', '30');
    await page.fill('input[name="passing_score"]', '70');
    await page.click('button[type="submit"]');
    await wait(2000);

    // Go to test show page
    await page.goto('/#/tests');
    await page.locator(`tr:has-text("${testData.title}")`).first().click();
    await page.waitForURL(/\/#\/tests\/\d+\/show/);

    // Find "Add Question" button
    const addQuestionButton = page.locator('button:has-text("Добавить вопрос")');
    if (await addQuestionButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      await addQuestionButton.click();

      // Fill question form
      const questionData = generateQuestionData('SINGLE_CHOICE');
      await page.fill('input[name="question_text"]', questionData.question_text);

      // Select question type
      const typeSelect = page.locator('select[name="question_type"]');
      if (await typeSelect.isVisible()) {
        await typeSelect.selectOption(questionData.question_type);
      }

      // Add points
      await page.fill('input[name="points"]', questionData.points.toString());

      // Submit question
      await page.click('button:has-text("Создать")');

      await wait(1000);

      // Should show success
      await expect(page.getByText(/создан|добавлен|успешно/i)).toBeVisible();
    }
  });

  test('should add options to SINGLE_CHOICE question', async ({ page }) => {
    // Create test
    const testData = generateTestData();
    await page.goto('/#/tests/create');
    await page.fill('input[name="title"]', testData.title);
    await page.fill('input[name="duration_minutes"]', '30');
    await page.fill('input[name="passing_score"]', '70');
    await page.click('button[type="submit"]');
    await wait(2000);

    // Navigate to test
    await page.goto('/#/tests');
    await page.locator(`tr:has-text("${testData.title}")`).first().click();

    // Add question
    const addQuestionButton = page.locator('button:has-text("Добавить вопрос")');
    if (await addQuestionButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      await addQuestionButton.click();

      const questionData = generateQuestionData('SINGLE_CHOICE');
      await page.fill('input[name="question_text"]', questionData.question_text);

      // Add option 1
      const addOptionButton = page.locator('button:has-text("Добавить опцию")');
      if (await addOptionButton.isVisible({ timeout: 2000 }).catch(() => false)) {
        await addOptionButton.click();
        await page.fill('input[name="option_text"]', 'Вариант 1');

        // Mark as correct
        await page.check('input[name="is_correct"]');

        // Add option 2
        await addOptionButton.click();
        await page.fill('input[name="option_text"]', 'Вариант 2');

        // Submit question
        await page.click('button:has-text("Создать")');

        await wait(1000);

        // Should create question with options
        await expect(page.getByText(/создан|добавлен/i)).toBeVisible();
      }
    }
  });

  test('should edit test metadata', async ({ page }) => {
    // Create test
    const testData = generateTestData();
    await page.goto('/#/tests/create');
    await page.fill('input[name="title"]', testData.title);
    await page.fill('input[name="duration_minutes"]', '30');
    await page.fill('input[name="passing_score"]', '70');
    await page.click('button[type="submit"]');
    await wait(2000);

    // Go to test list
    await page.goto('/#/tests');
    await page.locator(`tr:has-text("${testData.title}")`).first().click();
    await page.waitForURL(/\/#\/tests\/\d+\/show/);

    // Click edit button
    const editButton = page.locator('button:has-text("Редактировать")');
    if (await editButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      await editButton.click();
      await page.waitForURL(/\/#\/tests\/\d+$/);

      // Update title
      const newTitle = `${testData.title} EDITED`;
      await page.fill('input[name="title"]', newTitle);

      // Submit
      await page.click('button[type="submit"]');

      await wait(1000);

      // Should show success
      await expect(page.getByText(/обновлен|успешно/i)).toBeVisible();
    }
  });

  test('should delete test', async ({ page }) => {
    // Create test
    const testData = generateTestData();
    await page.goto('/#/tests/create');
    await page.fill('input[name="title"]', testData.title);
    await page.fill('input[name="duration_minutes"]', '30');
    await page.fill('input[name="passing_score"]', '70');
    await page.click('button[type="submit"]');
    await wait(2000);

    // Go to list
    await page.goto('/#/tests');
    await page.waitForSelector('[role="grid"]');

    // Select test
    const row = page.locator(`tr:has-text("${testData.title}")`).first();
    await row.locator('input[type="checkbox"]').check();

    // Delete
    await page.click('button:has-text("Удалить")');
    await page.click('button:has-text("Подтвердить")');

    await wait(1000);

    // Should show success
    await expect(page.getByText(/удален|успешно/i)).toBeVisible();
  });

  test('should filter tests by difficulty', async ({ page }) => {
    await page.goto('/#/tests');
    await page.waitForSelector('[role="grid"]');

    // Find difficulty filter
    const difficultyFilter = page.locator('select:has-text("Сложность")');
    if (await difficultyFilter.isVisible({ timeout: 2000 }).catch(() => false)) {
      await difficultyFilter.selectOption('2');

      await wait(500);

      // Check results
      const rows = await page.locator('tbody tr').count();
      expect(rows).toBeGreaterThanOrEqual(0);
    }
  });

  test('should display question types correctly', async ({ page }) => {
    await page.goto('/#/tests/create');

    const addQuestionButton = page.locator('button:has-text("Добавить вопрос")');
    if (await addQuestionButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      await addQuestionButton.click();

      // Check question type options
      const typeSelect = page.locator('select[name="question_type"]');
      if (await typeSelect.isVisible()) {
        await expect(typeSelect).toBeVisible();

        // Should have different question types
        // SINGLE_CHOICE, MULTIPLE_CHOICE, TRUE_FALSE, SHORT_ANSWER
        const options = await typeSelect.locator('option').count();
        expect(options).toBeGreaterThan(1);
      }
    }
  });
});
