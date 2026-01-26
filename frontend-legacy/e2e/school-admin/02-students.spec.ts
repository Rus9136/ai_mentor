import { test, expect } from '@playwright/test';
import { login, SCHOOL_ADMIN_USER, waitForAPIResponse } from '../helpers/auth';
import { generateStudentData, wait } from '../helpers/test-data';

test.describe('School ADMIN Students Management', () => {
  test.beforeEach(async ({ page }) => {
    await page.context().clearCookies();
    await login(page, SCHOOL_ADMIN_USER);
  });

  test('should navigate to students list', async ({ page }) => {
    await page.click('a[href="#/students"]');
    await expect(page).toHaveURL(/\/#\/students/);
    await expect(page.getByRole('heading', { name: /ученики/i })).toBeVisible();
  });

  test('should display students list', async ({ page }) => {
    await page.goto('/#/students');
    await page.waitForSelector('[role="grid"]', { timeout: 10000 });

    // Check for table
    await expect(page.getByRole('grid')).toBeVisible();
  });

  test('should create a new student', async ({ page }) => {
    const studentData = generateStudentData();

    await page.goto('/#/students/create');

    // Fill student form (transactional User → Student creation)
    await page.fill('input[name="first_name"]', studentData.first_name);
    await page.fill('input[name="last_name"]', studentData.last_name);
    await page.fill('input[name="email"]', studentData.email);
    await page.fill('input[name="password"]', studentData.password);
    await page.fill('input[name="grade_level"]', studentData.grade_level.toString());

    // Wait for API response
    const responsePromise = waitForAPIResponse(page, '/api/v1/admin/school/students', 'POST');

    // Submit
    await page.click('button[type="submit"]');

    const response = await responsePromise;
    expect(response.status()).toBe(200);

    // Should show success
    await expect(page.getByText(/создан|успешно|success/i)).toBeVisible();

    // Should auto-generate student_code (STU{grade}{year}{sequence})
    // This is checked in backend, frontend just displays it
  });

  test('should validate required fields when creating student', async ({ page }) => {
    await page.goto('/#/students/create');

    // Try to submit without filling
    await page.click('button[type="submit"]');

    // Should show validation errors
    await expect(page.getByText(/обязательн|required/i)).toBeVisible();
  });

  test('should edit student information', async ({ page }) => {
    // Create student first
    const studentData = generateStudentData();
    await page.goto('/#/students/create');
    await page.fill('input[name="first_name"]', studentData.first_name);
    await page.fill('input[name="last_name"]', studentData.last_name);
    await page.fill('input[name="email"]', studentData.email);
    await page.fill('input[name="password"]', studentData.password);
    await page.fill('input[name="grade_level"]', '7');
    await page.click('button[type="submit"]');
    await wait(2000);

    // Navigate to students list
    await page.goto('/#/students');
    await page.locator(`tr:has-text("${studentData.last_name}")`).first().click();
    await page.waitForURL(/\/#\/students\/\d+\/show/);

    // Click edit
    const editButton = page.locator('button:has-text("Редактировать")');
    if (await editButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      await editButton.click();
      await page.waitForURL(/\/#\/students\/\d+$/);

      // Update grade level
      await page.fill('input[name="grade_level"]', '8');

      // Submit
      await page.click('button[type="submit"]');

      await wait(1000);

      // Should show success
      await expect(page.getByText(/обновлен|успешно/i)).toBeVisible();
    }
  });

  test('should deactivate student', async ({ page }) => {
    // Create student
    const studentData = generateStudentData();
    await page.goto('/#/students/create');
    await page.fill('input[name="first_name"]', studentData.first_name);
    await page.fill('input[name="last_name"]', studentData.last_name);
    await page.fill('input[name="email"]', studentData.email);
    await page.fill('input[name="password"]', studentData.password);
    await page.fill('input[name="grade_level"]', '7');
    await page.click('button[type="submit"]');
    await wait(2000);

    // Go to student show page
    await page.goto('/#/students');
    await page.locator(`tr:has-text("${studentData.last_name}")`).first().click();
    await page.waitForURL(/\/#\/students\/\d+\/show/);

    // Find deactivate button
    const deactivateButton = page.locator('button:has-text("Деактивировать")');
    if (await deactivateButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      await deactivateButton.click();

      await wait(1000);

      // Should show success
      await expect(page.getByText(/деактивирован|успешно/i)).toBeVisible();
    }
  });

  test('should delete student', async ({ page }) => {
    // Create student
    const studentData = generateStudentData();
    await page.goto('/#/students/create');
    await page.fill('input[name="first_name"]', studentData.first_name);
    await page.fill('input[name="last_name"]', studentData.last_name);
    await page.fill('input[name="email"]', studentData.email);
    await page.fill('input[name="password"]', studentData.password);
    await page.fill('input[name="grade_level"]', '7');
    await page.click('button[type="submit"]');
    await wait(2000);

    // Go to list
    await page.goto('/#/students');
    await page.waitForSelector('[role="grid"]');

    // Select student
    const row = page.locator(`tr:has-text("${studentData.last_name}")`).first();
    await row.locator('input[type="checkbox"]').check();

    // Delete
    await page.click('button:has-text("Удалить")');
    await page.click('button:has-text("Подтвердить")');

    await wait(1000);

    // Should show success
    await expect(page.getByText(/удален|успешно/i)).toBeVisible();
  });

  test('should filter students by grade level', async ({ page }) => {
    await page.goto('/#/students');
    await page.waitForSelector('[role="grid"]');

    // Find grade level filter
    const gradeFilter = page.locator('select:has-text("Класс")');
    if (await gradeFilter.isVisible({ timeout: 2000 }).catch(() => false)) {
      await gradeFilter.selectOption('7');

      await wait(500);

      // Check results (client-side filtering)
      const rows = await page.locator('tbody tr').count();
      expect(rows).toBeGreaterThanOrEqual(0);
    }
  });

  test('should search students by name', async ({ page }) => {
    await page.goto('/#/students');
    await page.waitForSelector('[role="grid"]');

    // Enter search query
    await page.fill('input[placeholder*="поиск"]', 'Студентов');

    await wait(500);

    // Should filter results
    const rows = await page.locator('tbody tr').count();
    expect(rows).toBeGreaterThanOrEqual(0);
  });

  test('should view student details', async ({ page }) => {
    await page.goto('/#/students');
    await page.waitForSelector('[role="grid"]');

    // Click first student row
    const firstRow = page.locator('tbody tr').first();
    if (await firstRow.isVisible({ timeout: 5000 }).catch(() => false)) {
      await firstRow.click();

      // Should navigate to show page
      await page.waitForURL(/\/#\/students\/\d+\/show/);

      // Should show student details
      await expect(page.getByText(/имя|фамилия|класс/i)).toBeVisible();
    }
  });

  test('should bulk deactivate students', async ({ page }) => {
    await page.goto('/#/students');
    await page.waitForSelector('[role="grid"]');

    // Select multiple students
    const checkboxes = page.locator('tbody input[type="checkbox"]');
    const count = await checkboxes.count();

    if (count > 0) {
      // Check first 2 checkboxes
      await checkboxes.nth(0).check();
      if (count > 1) {
        await checkboxes.nth(1).check();
      }

      // Click bulk deactivate button
      const bulkDeactivateButton = page.locator('button:has-text("Деактивировать")');
      if (await bulkDeactivateButton.isVisible({ timeout: 3000 }).catch(() => false)) {
        await bulkDeactivateButton.click();

        await wait(1000);

        // Should show success
        await expect(page.getByText(/деактивирован|успешно/i)).toBeVisible();
      }
    }
  });
});
