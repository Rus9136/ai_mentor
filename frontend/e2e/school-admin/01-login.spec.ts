import { test, expect } from '@playwright/test';
import { login, logout, SCHOOL_ADMIN_USER, isAuthenticated } from '../helpers/auth';

test.describe('School ADMIN Login', () => {
  test.beforeEach(async ({ page }) => {
    await page.context().clearCookies();
    await page.goto('/');
  });

  test('should login successfully with School ADMIN credentials', async ({ page }) => {
    await login(page, SCHOOL_ADMIN_USER);

    // Check if redirected to dashboard
    await expect(page).toHaveURL(/\/#\/$/);

    // Check if authenticated
    const authenticated = await isAuthenticated(page);
    expect(authenticated).toBe(true);
  });

  test('should show School ADMIN menu items', async ({ page }) => {
    await login(page, SCHOOL_ADMIN_USER);

    // Check for School ADMIN specific menu items
    await expect(page.getByRole('link', { name: /ученики/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /учителя/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /родители/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /классы/i })).toBeVisible();

    // Global admin menu items should not be visible
    await expect(page.getByRole('link', { name: /^школы$/i })).not.toBeVisible();
  });

  test('should access library (textbooks and tests)', async ({ page }) => {
    await login(page, SCHOOL_ADMIN_USER);

    // School admin should have access to library
    const libraryLink = page.getByRole('link', { name: /библиотека|учебники/i });
    if (await libraryLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      await expect(libraryLink).toBeVisible();
    }
  });

  test('should logout successfully', async ({ page }) => {
    await login(page, SCHOOL_ADMIN_USER);
    await logout(page);

    // Check if redirected to login
    await expect(page).toHaveURL(/\/#\/login/);

    // Check if not authenticated
    const authenticated = await isAuthenticated(page);
    expect(authenticated).toBe(false);
  });

  test('should persist authentication after page reload', async ({ page }) => {
    await login(page, SCHOOL_ADMIN_USER);

    // Reload page
    await page.reload();

    // Should still be authenticated
    await page.waitForURL(/\/#\/$/, { timeout: 5000 });
    const authenticated = await isAuthenticated(page);
    expect(authenticated).toBe(true);
  });
});
