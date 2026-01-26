import { test, expect } from '@playwright/test';
import { login, logout, SUPER_ADMIN_USER, isAuthenticated } from '../helpers/auth';

test.describe('SUPER_ADMIN Login', () => {
  test.beforeEach(async ({ page }) => {
    // Clear storage before each test
    await page.context().clearCookies();
    await page.goto('/');
  });

  test('should display login page', async ({ page }) => {
    await expect(page).toHaveURL(/\/#\/login/);
    await expect(page.getByRole('heading', { name: /вход/i })).toBeVisible();
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByLabel(/пароль/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /войти/i })).toBeVisible();
  });

  test('should login successfully with valid credentials', async ({ page }) => {
    await login(page, SUPER_ADMIN_USER);

    // Check if redirected to dashboard
    await expect(page).toHaveURL(/\/#\/$/);

    // Check if user info is displayed
    await expect(page.getByText(/админ/i)).toBeVisible();

    // Check if authenticated
    const authenticated = await isAuthenticated(page);
    expect(authenticated).toBe(true);
  });

  test('should show error with invalid credentials', async ({ page }) => {
    await page.fill('input[name="username"]', 'invalid@test.com');
    await page.fill('input[name="password"]', 'wrongpassword');
    await page.click('button[type="submit"]');

    // Should still be on login page
    await expect(page).toHaveURL(/\/#\/login/);

    // Should show error notification
    await expect(page.getByText(/ошибка|неверн|incorrect/i)).toBeVisible();
  });

  test('should logout successfully', async ({ page }) => {
    // Login first
    await login(page, SUPER_ADMIN_USER);

    // Logout
    await logout(page);

    // Check if redirected to login
    await expect(page).toHaveURL(/\/#\/login/);

    // Check if not authenticated
    const authenticated = await isAuthenticated(page);
    expect(authenticated).toBe(false);
  });

  test('should persist authentication after page reload', async ({ page }) => {
    await login(page, SUPER_ADMIN_USER);

    // Reload page
    await page.reload();

    // Should still be on dashboard
    await page.waitForURL(/\/#\/$/, { timeout: 5000 });
    await expect(page).toHaveURL(/\/#\/$/);

    // Should still be authenticated
    const authenticated = await isAuthenticated(page);
    expect(authenticated).toBe(true);
  });

  test('should show SUPER_ADMIN menu items', async ({ page }) => {
    await login(page, SUPER_ADMIN_USER);

    // Check for SUPER_ADMIN specific menu items
    await expect(page.getByRole('link', { name: /школы/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /учебники/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /тесты/i })).toBeVisible();

    // School ADMIN menu items should not be visible
    await expect(page.getByRole('link', { name: /ученики/i })).not.toBeVisible();
    await expect(page.getByRole('link', { name: /учителя/i })).not.toBeVisible();
  });
});
