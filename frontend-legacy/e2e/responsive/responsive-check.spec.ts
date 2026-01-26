import { test, expect, devices } from '@playwright/test';
import { login, SUPER_ADMIN_USER, SCHOOL_ADMIN_USER } from '../helpers/auth';

/**
 * Responsive Design Tests
 *
 * Тестирование отзывчивости UI на различных разрешениях:
 * - Desktop: 1920x1080, 1366x768
 * - Tablet: iPad (768x1024), iPad Pro (1024x1366)
 * - Mobile: iPhone 12 (390x844), Pixel 5 (393x851)
 */

test.describe('Responsive Design - Desktop', () => {
  test('should display properly on 1920x1080 (Full HD)', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/');

    // Login
    await login(page, SUPER_ADMIN_USER);

    // Проверка sidebar (должен быть виден на desktop)
    const sidebar = page.locator('[role="navigation"]').first();
    await expect(sidebar).toBeVisible();

    // Проверка AppBar
    const appBar = page.locator('header[class*="MuiAppBar"]');
    await expect(appBar).toBeVisible();

    // Проверка списка школ
    await page.click('text=Школы');
    await page.waitForLoadState('networkidle');

    // Table должна быть видна
    const table = page.locator('table');
    await expect(table).toBeVisible();

    // Все колонки должны быть видны на большом экране
    await expect(page.locator('th:has-text("Название")')).toBeVisible();
    await expect(page.locator('th:has-text("Код")')).toBeVisible();
    await expect(page.locator('th:has-text("Регион")')).toBeVisible();
  });

  test('should display properly on 1366x768 (Laptop)', async ({ page }) => {
    await page.setViewportSize({ width: 1366, height: 768 });
    await page.goto('/');

    await login(page, SUPER_ADMIN_USER);

    // Sidebar должен быть виден
    const sidebar = page.locator('[role="navigation"]').first();
    await expect(sidebar).toBeVisible();

    // Контент не должен обрезаться
    await page.click('text=Школы');
    await page.waitForLoadState('networkidle');

    const table = page.locator('table');
    await expect(table).toBeVisible();
  });
});

test.describe('Responsive Design - Tablet', () => {
  test('should display properly on iPad (768x1024)', async ({ page }) => {
    // Используем preset от Playwright
    await page.setViewportSize(devices['iPad'].viewport);
    await page.goto('/');

    await login(page, SCHOOL_ADMIN_USER);

    // На планшете sidebar может быть скрыт в drawer
    // Проверяем, что есть menu button для открытия
    const menuButton = page.locator('button[aria-label*="menu"], button[aria-label*="Menu"]');

    // Если sidebar скрыт, проверяем menu button
    const sidebar = page.locator('[role="navigation"]').first();
    const isSidebarVisible = await sidebar.isVisible().catch(() => false);

    if (!isSidebarVisible) {
      await expect(menuButton).toBeVisible();
      // Открываем menu
      await menuButton.click();
      await expect(sidebar).toBeVisible();
    }

    // Навигация к ученикам
    await page.click('text=Ученики');
    await page.waitForLoadState('networkidle');

    // На планшете может использоваться SimpleList вместо таблицы
    // Проверяем, что контент отображается
    const contentArea = page.locator('main');
    await expect(contentArea).toBeVisible();
  });

  test('should display properly on iPad Pro (1024x1366)', async ({ page }) => {
    await page.setViewportSize(devices['iPad Pro'].viewport);
    await page.goto('/');

    await login(page, SCHOOL_ADMIN_USER);

    // На iPad Pro sidebar обычно виден
    const sidebar = page.locator('[role="navigation"]').first();
    await expect(sidebar).toBeVisible();

    await page.click('text=Классы');
    await page.waitForLoadState('networkidle');

    // Table должна быть видна
    const table = page.locator('table');
    await expect(table).toBeVisible();
  });
});

test.describe('Responsive Design - Mobile', () => {
  test('should display properly on iPhone 12 (390x844)', async ({ page }) => {
    await page.setViewportSize(devices['iPhone 12'].viewport);
    await page.goto('/');

    await login(page, SCHOOL_ADMIN_USER);

    // На мобильном sidebar точно скрыт
    const menuButton = page.locator('button[aria-label*="menu"], button[aria-label*="Menu"]').first();
    await expect(menuButton).toBeVisible();

    // Открываем menu
    await menuButton.click();

    // Drawer должен появиться
    const drawer = page.locator('[role="presentation"], [class*="MuiDrawer"]');
    await expect(drawer).toBeVisible();

    // Кликаем на Ученики
    await page.click('text=Ученики');
    await page.waitForLoadState('networkidle');

    // Закрываем drawer (может закрыться автоматически)

    // На мобильном должен использоваться SimpleList
    // Проверяем, что список отображается
    const list = page.locator('[role="list"], [class*="MuiList"]');
    await expect(list).toBeVisible();

    // Кнопки должны быть достаточно большими для touch (минимум 44x44px)
    const createButton = page.locator('button:has-text("Создать"), a[aria-label*="Create"], a[aria-label*="create"]').first();
    if (await createButton.isVisible()) {
      const buttonBox = await createButton.boundingBox();
      if (buttonBox) {
        expect(buttonBox.width).toBeGreaterThanOrEqual(44);
        expect(buttonBox.height).toBeGreaterThanOrEqual(44);
      }
    }
  });

  test('should display properly on Pixel 5 (393x851)', async ({ page }) => {
    await page.setViewportSize(devices['Pixel 5'].viewport);
    await page.goto('/');

    await login(page, SUPER_ADMIN_USER);

    // Menu button должен быть виден
    const menuButton = page.locator('button[aria-label*="menu"], button[aria-label*="Menu"]').first();
    await expect(menuButton).toBeVisible();

    // Открываем drawer
    await menuButton.click();

    // Навигация к школам
    await page.click('text=Школы');
    await page.waitForLoadState('networkidle');

    // SimpleList должен использоваться на мобильном
    const contentArea = page.locator('main');
    await expect(contentArea).toBeVisible();

    // Проверка, что текст не обрезается
    // (визуально проверяется через screenshot)
  });

  test('should handle form inputs on mobile', async ({ page }) => {
    await page.setViewportSize(devices['iPhone 12'].viewport);
    await page.goto('/');

    await login(page, SCHOOL_ADMIN_USER);

    // Открываем menu
    const menuButton = page.locator('button[aria-label*="menu"], button[aria-label*="Menu"]').first();
    await menuButton.click();

    // Переход к созданию ученика
    await page.click('text=Ученики');
    await page.waitForLoadState('networkidle');

    // Ищем кнопку создания (может быть FAB или обычная кнопка)
    const createButton = page.locator('a[href*="/students/create"], button:has-text("Создать")').first();
    if (await createButton.isVisible()) {
      await createButton.click();
      await page.waitForLoadState('networkidle');

      // Поля ввода должны быть достаточно большими
      const firstInput = page.locator('input[type="text"], input[type="email"]').first();
      if (await firstInput.isVisible()) {
        const inputBox = await firstInput.boundingBox();
        if (inputBox) {
          // Минимальная высота для touch-friendly input
          expect(inputBox.height).toBeGreaterThanOrEqual(40);
        }
      }
    }
  });
});

test.describe('Responsive Design - Screenshots', () => {
  test('take screenshots on different viewports', async ({ page }) => {
    await page.goto('/');
    await login(page, SUPER_ADMIN_USER);
    await page.click('text=Школы');
    await page.waitForLoadState('networkidle');

    // Desktop
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.screenshot({ path: 'screenshots/desktop-1920.png', fullPage: true });

    // Laptop
    await page.setViewportSize({ width: 1366, height: 768 });
    await page.screenshot({ path: 'screenshots/laptop-1366.png', fullPage: true });

    // Tablet
    await page.setViewportSize(devices['iPad'].viewport);
    await page.screenshot({ path: 'screenshots/tablet-ipad.png', fullPage: true });

    // Mobile
    await page.setViewportSize(devices['iPhone 12'].viewport);
    await page.screenshot({ path: 'screenshots/mobile-iphone12.png', fullPage: true });
  });
});
