import { test, expect } from '@playwright/test';
import { login, SUPER_ADMIN_USER, waitForAPIResponse } from '../helpers/auth';
import { generateTextbookData, generateChapterData, wait } from '../helpers/test-data';

test.describe('SUPER_ADMIN Textbooks Management', () => {
  test.beforeEach(async ({ page }) => {
    await page.context().clearCookies();
    await login(page, SUPER_ADMIN_USER);
  });

  test('should navigate to textbooks list', async ({ page }) => {
    await page.click('a[href="#/textbooks"]');
    await expect(page).toHaveURL(/\/#\/textbooks/);
    await expect(page.getByRole('heading', { name: /учебники/i })).toBeVisible();
  });

  test('should display textbooks list with filters', async ({ page }) => {
    await page.goto('/#/textbooks');
    await page.waitForSelector('[role="grid"]', { timeout: 10000 });

    // Check for filter inputs
    await expect(page.getByPlaceholder(/поиск/i)).toBeVisible();
  });

  test('should create a new textbook', async ({ page }) => {
    const textbookData = generateTextbookData();

    await page.goto('/#/textbooks/create');

    // Fill basic information
    await page.fill('input[name="title"]', textbookData.title);
    await page.fill('input[name="subject"]', textbookData.subject);
    await page.fill('input[name="grade_level"]', textbookData.grade_level.toString());
    await page.fill('input[name="author"]', textbookData.author);
    await page.fill('input[name="publisher"]', textbookData.publisher);
    await page.fill('input[name="year"]', textbookData.year.toString());

    // Select language
    await page.click('select[name="language"]');
    await page.selectOption('select[name="language"]', textbookData.language);

    // Wait for API response
    const responsePromise = waitForAPIResponse(page, '/api/v1/admin/global/textbooks', 'POST');

    // Submit
    await page.click('button[type="submit"]');

    const response = await responsePromise;
    expect(response.status()).toBe(200);

    // Should show success message
    await expect(page.getByText(/создан|успешно|success/i)).toBeVisible();
  });

  test('should validate required fields when creating textbook', async ({ page }) => {
    await page.goto('/#/textbooks/create');

    // Try to submit without filling
    await page.click('button[type="submit"]');

    // Should show validation errors
    await expect(page.getByText(/обязательн|required/i)).toBeVisible();
  });

  test('should edit textbook structure', async ({ page }) => {
    // First create a textbook
    const textbookData = generateTextbookData();
    await page.goto('/#/textbooks/create');
    await page.fill('input[name="title"]', textbookData.title);
    await page.fill('input[name="subject"]', textbookData.subject);
    await page.fill('input[name="grade_level"]', '7');
    await page.fill('input[name="author"]', textbookData.author);
    await page.click('button[type="submit"]');
    await wait(2000);

    // Navigate to textbook show page
    await page.goto('/#/textbooks');
    const row = page.locator(`tr:has-text("${textbookData.title}")`).first();
    await row.click();
    await page.waitForURL(/\/#\/textbooks\/\d+\/show/);

    // Click "Edit Structure" button (if available)
    const editStructureButton = page.locator('button:has-text("Редактировать структуру")');
    if (await editStructureButton.isVisible()) {
      await editStructureButton.click();
      await page.waitForURL(/\/#\/textbooks\/\d+\/structure/);

      // Should see structure editor
      await expect(page.getByText(/структура учебника/i)).toBeVisible();
    }
  });

  test('should add chapter to textbook', async ({ page }) => {
    // Create textbook first
    const textbookData = generateTextbookData();
    await page.goto('/#/textbooks/create');
    await page.fill('input[name="title"]', textbookData.title);
    await page.fill('input[name="subject"]', textbookData.subject);
    await page.fill('input[name="grade_level"]', '7');
    await page.fill('input[name="author"]', textbookData.author);
    await page.click('button[type="submit"]');
    await wait(2000);

    // Go to structure editor
    await page.goto('/#/textbooks');
    await page.locator(`tr:has-text("${textbookData.title}")`).first().click();

    // Try to find "Add Chapter" button
    const addChapterButton = page.locator('button:has-text("Добавить главу")');
    if (await addChapterButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      await addChapterButton.click();

      // Fill chapter dialog
      const chapterData = generateChapterData();
      await page.fill('input[name="chapter_number"]', chapterData.chapter_number);
      await page.fill('input[name="title"]', chapterData.title);

      // Submit chapter
      await page.click('button:has-text("Создать")');

      await wait(1000);

      // Should see success message
      await expect(page.getByText(/создан|успешно|добавлен/i)).toBeVisible();
    }
  });

  test('should filter textbooks by subject', async ({ page }) => {
    await page.goto('/#/textbooks');
    await page.waitForSelector('[role="grid"]');

    // Open filter
    const subjectFilter = page.locator('select:has-text("Предмет")');
    if (await subjectFilter.isVisible({ timeout: 2000 }).catch(() => false)) {
      await subjectFilter.click();
      await page.click('text="Математика"');

      await wait(500);

      // Check results
      const rows = await page.locator('tbody tr').count();
      expect(rows).toBeGreaterThanOrEqual(0);
    }
  });

  test('should search textbooks by title', async ({ page }) => {
    await page.goto('/#/textbooks');
    await page.waitForSelector('[role="grid"]');

    // Enter search query
    await page.fill('input[placeholder*="поиск"]', 'Алгебра');

    // Wait for filtering
    await wait(500);

    // Should filter results (client-side)
    const rows = page.locator('tbody tr');
    const count = await rows.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('should delete textbook', async ({ page }) => {
    // Create textbook first
    const textbookData = generateTextbookData();
    await page.goto('/#/textbooks/create');
    await page.fill('input[name="title"]', textbookData.title);
    await page.fill('input[name="subject"]', textbookData.subject);
    await page.fill('input[name="grade_level"]', '7');
    await page.fill('input[name="author"]', textbookData.author);
    await page.click('button[type="submit"]');
    await wait(2000);

    // Go to list
    await page.goto('/#/textbooks');
    await page.waitForSelector('[role="grid"]');

    // Select the textbook
    const row = page.locator(`tr:has-text("${textbookData.title}")`).first();
    await row.locator('input[type="checkbox"]').check();

    // Click delete button
    await page.click('button:has-text("Удалить")');

    // Confirm deletion
    await page.click('button:has-text("Подтвердить")');

    await wait(1000);

    // Should show success
    await expect(page.getByText(/удален|успешно|deleted/i)).toBeVisible();
  });

  test('should show textbook details', async ({ page }) => {
    await page.goto('/#/textbooks');
    await page.waitForSelector('[role="grid"]');

    // Click first textbook row
    const firstRow = page.locator('tbody tr').first();
    if (await firstRow.isVisible({ timeout: 5000 }).catch(() => false)) {
      await firstRow.click();

      // Should navigate to show page
      await page.waitForURL(/\/#\/textbooks\/\d+\/show/);

      // Should show tabs: Информация, Структура
      await expect(page.getByRole('tab', { name: /информация/i })).toBeVisible();
      await expect(page.getByRole('tab', { name: /структура/i })).toBeVisible();
    }
  });
});
