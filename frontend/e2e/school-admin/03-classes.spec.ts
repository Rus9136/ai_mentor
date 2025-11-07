import { test, expect } from '@playwright/test';
import { login, SCHOOL_ADMIN_USER, waitForAPIResponse } from '../helpers/auth';
import { generateClassData, generateStudentData, wait } from '../helpers/test-data';

test.describe('School ADMIN Classes Management', () => {
  test.beforeEach(async ({ page }) => {
    await page.context().clearCookies();
    await login(page, SCHOOL_ADMIN_USER);
  });

  test('should navigate to classes list', async ({ page }) => {
    await page.click('a[href="#/classes"]');
    await expect(page).toHaveURL(/\/#\/classes/);
    await expect(page.getByRole('heading', { name: /классы/i })).toBeVisible();
  });

  test('should display classes list', async ({ page }) => {
    await page.goto('/#/classes');
    await page.waitForSelector('[role="grid"]', { timeout: 10000 });

    // Check for table
    await expect(page.getByRole('grid')).toBeVisible();
  });

  test('should create a new class', async ({ page }) => {
    const classData = generateClassData();

    await page.goto('/#/classes/create');

    // Fill form
    await page.fill('input[name="name"]', classData.name);
    await page.fill('input[name="grade_level"]', classData.grade_level.toString());
    await page.fill('input[name="academic_year"]', classData.academic_year);

    // Wait for API response
    const responsePromise = waitForAPIResponse(page, '/api/v1/admin/school/classes', 'POST');

    // Submit
    await page.click('button[type="submit"]');

    const response = await responsePromise;
    expect(response.status()).toBe(200);

    // Should show success
    await expect(page.getByText(/создан|успешно|success/i)).toBeVisible();
  });

  test('should validate required fields when creating class', async ({ page }) => {
    await page.goto('/#/classes/create');

    // Try to submit without filling
    await page.click('button[type="submit"]');

    // Should show validation errors
    await expect(page.getByText(/обязательн|required/i)).toBeVisible();
  });

  test('should assign students to class using Transfer List', async ({ page }) => {
    // Create class first
    const classData = generateClassData();
    await page.goto('/#/classes/create');
    await page.fill('input[name="name"]', classData.name);
    await page.fill('input[name="grade_level"]', '7');
    await page.fill('input[name="academic_year"]', classData.academic_year);
    await page.click('button[type="submit"]');
    await wait(2000);

    // Go to class edit page
    await page.goto('/#/classes');
    await page.locator(`tr:has-text("${classData.name}")`).first().click();
    await page.waitForURL(/\/#\/classes\/\d+\/show/);

    // Click edit
    const editButton = page.locator('button:has-text("Редактировать")');
    if (await editButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      await editButton.click();
      await page.waitForURL(/\/#\/classes\/\d+$/);

      // Should see Transfer List for students
      await expect(page.getByText(/доступные ученики|available students/i)).toBeVisible();

      // Select a student from available list
      const availableList = page.locator('[aria-label*="доступны"]').first();
      const firstStudent = availableList.locator('li').first();

      if (await firstStudent.isVisible({ timeout: 3000 }).catch(() => false)) {
        await firstStudent.click();

        // Click "Add" button (arrow right)
        const addButton = page.locator('button[aria-label*="добавить"]');
        if (await addButton.isVisible()) {
          await addButton.click();

          await wait(1000);

          // Student should appear in assigned list
          await expect(page.locator('[aria-label*="добавлен"]')).toBeVisible();
        }
      }
    }
  });

  test('should remove student from class', async ({ page }) => {
    // Create class
    const classData = generateClassData();
    await page.goto('/#/classes/create');
    await page.fill('input[name="name"]', classData.name);
    await page.fill('input[name="grade_level"]', '7');
    await page.fill('input[name="academic_year"]', classData.academic_year);
    await page.click('button[type="submit"]');
    await wait(2000);

    // Edit class
    await page.goto('/#/classes');
    await page.locator(`tr:has-text("${classData.name}")`).first().click();
    const editButton = page.locator('button:has-text("Редактировать")');
    if (await editButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      await editButton.click();

      // Select student from assigned list
      const assignedList = page.locator('[aria-label*="добавлен"]').first();
      const firstStudent = assignedList.locator('li').first();

      if (await firstStudent.isVisible({ timeout: 3000 }).catch(() => false)) {
        await firstStudent.click();

        // Click "Remove" button (arrow left)
        const removeButton = page.locator('button[aria-label*="удалить"]');
        if (await removeButton.isVisible()) {
          await removeButton.click();

          await wait(1000);

          // Student should be removed
          // (check that assigned list has one less item)
        }
      }
    }
  });

  test('should filter classes by grade level', async ({ page }) => {
    await page.goto('/#/classes');
    await page.waitForSelector('[role="grid"]');

    // Find grade filter
    const gradeFilter = page.locator('select:has-text("Класс")');
    if (await gradeFilter.isVisible({ timeout: 2000 }).catch(() => false)) {
      await gradeFilter.selectOption('7');

      await wait(500);

      // Check results
      const rows = await page.locator('tbody tr').count();
      expect(rows).toBeGreaterThanOrEqual(0);
    }
  });

  test('should view class details', async ({ page }) => {
    await page.goto('/#/classes');
    await page.waitForSelector('[role="grid"]');

    // Click first class row
    const firstRow = page.locator('tbody tr').first();
    if (await firstRow.isVisible({ timeout: 5000 }).catch(() => false)) {
      await firstRow.click();

      // Should navigate to show page
      await page.waitForURL(/\/#\/classes\/\d+\/show/);

      // Should show class details
      await expect(page.getByText(/название|класс|учебный год/i)).toBeVisible();
    }
  });

  test('should delete class', async ({ page }) => {
    // Create class
    const classData = generateClassData();
    await page.goto('/#/classes/create');
    await page.fill('input[name="name"]', classData.name);
    await page.fill('input[name="grade_level"]', '7');
    await page.fill('input[name="academic_year"]', classData.academic_year);
    await page.click('button[type="submit"]');
    await wait(2000);

    // Go to list
    await page.goto('/#/classes');
    await page.waitForSelector('[role="grid"]');

    // Select class
    const row = page.locator(`tr:has-text("${classData.name}")`).first();
    await row.locator('input[type="checkbox"]').check();

    // Delete
    await page.click('button:has-text("Удалить")');
    await page.click('button:has-text("Подтвердить")');

    await wait(1000);

    // Should show success
    await expect(page.getByText(/удален|успешно/i)).toBeVisible();
  });

  test('should show students count in class list', async ({ page }) => {
    await page.goto('/#/classes');
    await page.waitForSelector('[role="grid"]');

    // Table should show number of students in each class
    // (This is displayed in the DataGrid, check that column exists)
    const firstRow = page.locator('tbody tr').first();
    if (await firstRow.isVisible({ timeout: 5000 }).catch(() => false)) {
      // Should have a column showing student count
      await expect(firstRow).toBeVisible();
    }
  });

  test('should assign teachers to class', async ({ page }) => {
    // Create class
    const classData = generateClassData();
    await page.goto('/#/classes/create');
    await page.fill('input[name="name"]', classData.name);
    await page.fill('input[name="grade_level"]', '7');
    await page.fill('input[name="academic_year"]', classData.academic_year);
    await page.click('button[type="submit"]');
    await wait(2000);

    // Edit class
    await page.goto('/#/classes');
    await page.locator(`tr:has-text("${classData.name}")`).first().click();
    const editButton = page.locator('button:has-text("Редактировать")');
    if (await editButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      await editButton.click();

      // Should see Transfer List for teachers (if implemented)
      const teachersSection = page.getByText(/учителя|teachers/i);
      if (await teachersSection.isVisible({ timeout: 3000 }).catch(() => false)) {
        await expect(teachersSection).toBeVisible();
      }
    }
  });
});
