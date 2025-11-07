import { test, expect } from '@playwright/test';
import { login, SUPER_ADMIN_USER, waitForAPIResponse } from '../helpers/auth';
import { generateSchoolData, wait } from '../helpers/test-data';

test.describe('SUPER_ADMIN Schools Management', () => {
  test.beforeEach(async ({ page }) => {
    await page.context().clearCookies();
    await login(page, SUPER_ADMIN_USER);
  });

  test('should navigate to schools list', async ({ page }) => {
    await page.click('a[href="#/schools"]');
    await expect(page).toHaveURL(/\/#\/schools/);
    await expect(page.getByRole('heading', { name: /школы/i })).toBeVisible();
  });

  test('should display schools list with data grid', async ({ page }) => {
    await page.goto('/#/schools');
    await page.waitForSelector('[role="grid"]', { timeout: 10000 });

    // Check for table headers
    await expect(page.getByText(/название/i)).toBeVisible();
    await expect(page.getByText(/код/i)).toBeVisible();
    await expect(page.getByText(/регион/i)).toBeVisible();
  });

  test('should create a new school', async ({ page }) => {
    const schoolData = generateSchoolData();

    // Navigate to schools
    await page.goto('/#/schools');
    await page.waitForLoadState('networkidle');

    // Click create button
    await page.click('a[href="#/schools/create"]');
    await expect(page).toHaveURL(/\/#\/schools\/create/);

    // Fill form
    await page.fill('input[name="name"]', schoolData.name);
    await page.fill('input[name="code"]', schoolData.code);
    await page.fill('input[name="region"]', schoolData.region);

    // Select license type
    await page.click('div[role="combobox"]'); // License type dropdown
    await page.click(`text="${schoolData.license_type}"`);

    // Wait for API response
    const responsePromise = waitForAPIResponse(page, '/api/v1/admin/schools', 'POST');

    // Submit form
    await page.click('button[type="submit"]');

    // Wait for response
    const response = await responsePromise;
    expect(response.status()).toBe(200);

    // Should redirect to school list or show page
    await page.waitForURL(/\/#\/schools/, { timeout: 5000 });

    // Check for success notification
    await expect(page.getByText(/создан|успешно|success/i)).toBeVisible();
  });

  test('should validate required fields when creating school', async ({ page }) => {
    await page.goto('/#/schools/create');

    // Try to submit without filling required fields
    await page.click('button[type="submit"]');

    // Should show validation errors
    await expect(page.getByText(/обязательн|required/i)).toBeVisible();
  });

  test('should edit existing school', async ({ page }) => {
    // First, create a school
    const schoolData = generateSchoolData();
    await page.goto('/#/schools/create');
    await page.fill('input[name="name"]', schoolData.name);
    await page.fill('input[name="code"]', schoolData.code);
    await page.fill('input[name="region"]', schoolData.region);
    await page.click('button[type="submit"]');
    await wait(2000);

    // Navigate back to schools list
    await page.goto('/#/schools');
    await page.waitForSelector('[role="grid"]');

    // Find and click the created school row
    const row = page.locator(`tr:has-text("${schoolData.name}")`).first();
    await row.click();

    // Wait for show page to load
    await page.waitForURL(/\/#\/schools\/\d+\/show/, { timeout: 5000 });

    // Click edit button
    await page.click('button:has-text("Редактировать")');
    await page.waitForURL(/\/#\/schools\/\d+/, { timeout: 5000 });

    // Update name
    const newName = `${schoolData.name} EDITED`;
    await page.fill('input[name="name"]', newName);

    // Submit
    const responsePromise = waitForAPIResponse(page, /\/api\/v1\/admin\/schools\/\d+/, 'PUT');
    await page.click('button[type="submit"]');
    const response = await responsePromise;
    expect(response.status()).toBe(200);

    // Check for success notification
    await expect(page.getByText(/обновлен|успешно|updated/i)).toBeVisible();
  });

  test('should delete school', async ({ page }) => {
    // Create a school first
    const schoolData = generateSchoolData();
    await page.goto('/#/schools/create');
    await page.fill('input[name="name"]', schoolData.name);
    await page.fill('input[name="code"]', schoolData.code);
    await page.fill('input[name="region"]', schoolData.region);
    await page.click('button[type="submit"]');
    await wait(2000);

    // Navigate to schools list
    await page.goto('/#/schools');
    await page.waitForSelector('[role="grid"]');

    // Select the school checkbox
    const row = page.locator(`tr:has-text("${schoolData.name}")`).first();
    await row.locator('input[type="checkbox"]').check();

    // Click delete button
    await page.click('button:has-text("Удалить")');

    // Confirm deletion in dialog
    await page.click('button:has-text("Подтвердить")');

    // Wait for API response
    await wait(1000);

    // Check for success notification
    await expect(page.getByText(/удален|успешно|deleted/i)).toBeVisible();
  });

  test('should block/unblock school', async ({ page }) => {
    // Create a school first
    const schoolData = generateSchoolData();
    await page.goto('/#/schools/create');
    await page.fill('input[name="name"]', schoolData.name);
    await page.fill('input[name="code"]', schoolData.code);
    await page.fill('input[name="region"]', schoolData.region);
    await page.click('button[type="submit"]');
    await wait(2000);

    // Navigate to school show page
    await page.goto('/#/schools');
    const row = page.locator(`tr:has-text("${schoolData.name}")`).first();
    await row.click();
    await page.waitForURL(/\/#\/schools\/\d+\/show/);

    // Find and click block button
    const blockButton = page.locator('button:has-text("Заблокировать")');
    if (await blockButton.isVisible()) {
      await blockButton.click();
      await expect(page.getByText(/заблокирован|blocked/i)).toBeVisible();

      // Now unblock
      await page.click('button:has-text("Разблокировать")');
      await expect(page.getByText(/разблокирован|unblocked/i)).toBeVisible();
    }
  });

  test('should filter schools by region', async ({ page }) => {
    await page.goto('/#/schools');
    await page.waitForSelector('[role="grid"]');

    // Open filter
    await page.click('button:has-text("Фильтр")');

    // Enter region filter
    await page.fill('input[placeholder*="регион"]', 'Алматы');

    // Apply filter (press Enter or click outside)
    await page.keyboard.press('Enter');

    await wait(500);

    // Check that filtered results are displayed
    // (This is client-side filtering, so check if table updates)
    const rows = await page.locator('tbody tr').count();
    expect(rows).toBeGreaterThan(0);
  });
});
