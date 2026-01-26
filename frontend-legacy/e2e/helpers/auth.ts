import { Page } from '@playwright/test';

export interface LoginCredentials {
  email: string;
  password: string;
}

/**
 * Test users credentials
 */
export const SUPER_ADMIN_USER: LoginCredentials = {
  email: 'admin@test.com',
  password: 'admin123',
};

export const SCHOOL_ADMIN_USER: LoginCredentials = {
  email: 'school.admin@test.com',
  password: 'admin123',
};

/**
 * Login helper function
 */
export async function login(page: Page, credentials: LoginCredentials) {
  await page.goto('/');

  // Wait for login form
  await page.waitForSelector('input[name="username"]', { timeout: 10000 });

  // Fill login form
  await page.fill('input[name="username"]', credentials.email);
  await page.fill('input[name="password"]', credentials.password);

  // Submit form
  await page.click('button[type="submit"]');

  // Wait for dashboard to load
  await page.waitForURL(/\/#\/$/, { timeout: 15000 });

  // Wait for dashboard to fully render
  await page.waitForLoadState('networkidle');
}

/**
 * Logout helper function
 */
export async function logout(page: Page) {
  // Click user menu button
  await page.click('button[aria-label="Профиль"]');

  // Click logout button
  await page.click('text="Выйти"');

  // Wait for redirect to login
  await page.waitForURL(/\/#\/login/, { timeout: 5000 });
}

/**
 * Check if user is authenticated
 */
export async function isAuthenticated(page: Page): Promise<boolean> {
  const accessToken = await page.evaluate(() => {
    return localStorage.getItem('access_token');
  });

  return !!accessToken;
}

/**
 * Wait for API response
 */
export async function waitForAPIResponse(
  page: Page,
  urlPattern: string | RegExp,
  method: string = 'GET'
) {
  return page.waitForResponse(
    (response) => {
      const url = response.url();
      const matchesURL = typeof urlPattern === 'string'
        ? url.includes(urlPattern)
        : urlPattern.test(url);
      return matchesURL && response.request().method() === method;
    },
    { timeout: 10000 }
  );
}
