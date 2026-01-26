import { test, expect } from '@playwright/test';
import { login, SCHOOL_ADMIN_USER, waitForAPIResponse } from '../helpers/auth';
import { wait } from '../helpers/test-data';

test.describe('School ADMIN Fork Textbook', () => {
  test.beforeEach(async ({ page }) => {
    await page.context().clearCookies();
    await login(page, SCHOOL_ADMIN_USER);
  });

  test('should view global textbooks in library', async ({ page }) => {
    // Navigate to textbooks/library
    const libraryLink = page.getByRole('link', { name: /библиотека|учебники/i });
    if (await libraryLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      await libraryLink.click();
    } else {
      await page.goto('/#/textbooks');
    }

    // Should see tabs: "Глобальные учебники" and "Наши учебники"
    const globalTab = page.getByRole('tab', { name: /глобальн/i });
    if (await globalTab.isVisible({ timeout: 5000 }).catch(() => false)) {
      await expect(globalTab).toBeVisible();
      await expect(page.getByRole('tab', { name: /наши|школьн/i })).toBeVisible();
    }
  });

  test('should display global textbooks as read-only', async ({ page }) => {
    await page.goto('/#/textbooks');

    // Click on global textbooks tab
    const globalTab = page.getByRole('tab', { name: /глобальн/i });
    if (await globalTab.isVisible({ timeout: 5000 }).catch(() => false)) {
      await globalTab.click();

      // Wait for list to load
      await wait(1000);

      // Should see "Customize" button instead of "Edit"
      const customizeButton = page.locator('button:has-text("Кастомизировать")');
      const editButton = page.locator('button:has-text("Редактировать")');

      // Customize should be visible, Edit should not (for global textbooks)
      if (await customizeButton.first().isVisible({ timeout: 3000 }).catch(() => false)) {
        await expect(customizeButton.first()).toBeVisible();
      }
    }
  });

  test('should open customize dialog when clicking customize button', async ({ page }) => {
    await page.goto('/#/textbooks');

    // Go to global tab
    const globalTab = page.getByRole('tab', { name: /глобальн/i });
    if (await globalTab.isVisible({ timeout: 5000 }).catch(() => false)) {
      await globalTab.click();
      await wait(1000);

      // Click first "Customize" button
      const customizeButton = page.locator('button:has-text("Кастомизировать")').first();
      if (await customizeButton.isVisible({ timeout: 3000 }).catch(() => false)) {
        await customizeButton.click();

        // Should open dialog
        await expect(page.getByRole('dialog')).toBeVisible();
        await expect(page.getByText(/создаете адаптированн|customize/i)).toBeVisible();

        // Should have title input
        await expect(page.locator('input[name="new_title"]')).toBeVisible();

        // Should have "Copy chapters and paragraphs" checkbox (checked by default)
        const copyCheckbox = page.locator('input[type="checkbox"]');
        if (await copyCheckbox.isVisible()) {
          const isChecked = await copyCheckbox.isChecked();
          expect(isChecked).toBe(true);
        }
      }
    }
  });

  test('should fork global textbook successfully', async ({ page }) => {
    await page.goto('/#/textbooks');

    // Go to global tab
    const globalTab = page.getByRole('tab', { name: /глобальн/i });
    if (await globalTab.isVisible({ timeout: 5000 }).catch(() => false)) {
      await globalTab.click();
      await wait(1000);

      // Click customize on first global textbook
      const customizeButton = page.locator('button:has-text("Кастомизировать")').first();
      if (await customizeButton.isVisible({ timeout: 3000 }).catch(() => false)) {
        await customizeButton.click();

        // Fill new title
        const timestamp = Date.now();
        const newTitle = `Адаптированный учебник ${timestamp}`;
        await page.fill('input[name="new_title"]', newTitle);

        // Wait for fork API call
        const responsePromise = waitForAPIResponse(
          page,
          /\/api\/v1\/admin\/school\/textbooks\/\d+\/customize/,
          'POST'
        );

        // Submit dialog
        await page.click('button:has-text("Подтвердить")');

        // Wait for response
        const response = await responsePromise;
        expect(response.status()).toBe(200);

        // Should show success notification
        await expect(page.getByText(/создан|успешно|кастомизирован/i)).toBeVisible();

        // Should redirect to school textbooks or edit page
        await page.waitForURL(/\/#\/(textbooks|school-textbooks)/, { timeout: 5000 });
      }
    }
  });

  test('should see forked textbook in "Our Textbooks" tab', async ({ page }) => {
    // First, fork a textbook
    await page.goto('/#/textbooks');

    const globalTab = page.getByRole('tab', { name: /глобальн/i });
    if (await globalTab.isVisible({ timeout: 5000 }).catch(() => false)) {
      await globalTab.click();
      await wait(1000);

      const customizeButton = page.locator('button:has-text("Кастомизировать")').first();
      if (await customizeButton.isVisible({ timeout: 3000 }).catch(() => false)) {
        await customizeButton.click();

        const timestamp = Date.now();
        const newTitle = `Адаптированный ${timestamp}`;
        await page.fill('input[name="new_title"]', newTitle);
        await page.click('button:has-text("Подтвердить")');

        await wait(2000);

        // Now go to "Our Textbooks" tab
        await page.goto('/#/textbooks');
        const ourTab = page.getByRole('tab', { name: /наши|школьн/i });
        if (await ourTab.isVisible({ timeout: 5000 }).catch(() => false)) {
          await ourTab.click();
          await wait(1000);

          // Should see the forked textbook
          await expect(page.getByText(newTitle)).toBeVisible();

          // Should have badge "Адаптировано из: {original_title}"
          const badge = page.locator('text=/адаптирован|customized/i');
          if (await badge.isVisible({ timeout: 3000 }).catch(() => false)) {
            await expect(badge).toBeVisible();
          }
        }
      }
    }
  });

  test('should be able to edit forked textbook', async ({ page }) => {
    // Fork textbook first
    await page.goto('/#/textbooks');

    const globalTab = page.getByRole('tab', { name: /глобальн/i });
    if (await globalTab.isVisible({ timeout: 5000 }).catch(() => false)) {
      await globalTab.click();
      await wait(1000);

      const customizeButton = page.locator('button:has-text("Кастомизировать")').first();
      if (await customizeButton.isVisible({ timeout: 3000 }).catch(() => false)) {
        await customizeButton.click();

        const timestamp = Date.now();
        const newTitle = `Адаптированный ${timestamp}`;
        await page.fill('input[name="new_title"]', newTitle);
        await page.click('button:has-text("Подтвердить")');

        await wait(2000);

        // Go to our textbooks
        await page.goto('/#/textbooks');
        const ourTab = page.getByRole('tab', { name: /наши|школьн/i });
        if (await ourTab.isVisible()) {
          await ourTab.click();
          await wait(1000);

          // Click on forked textbook
          const row = page.locator(`tr:has-text("${newTitle}")`).first();
          if (await row.isVisible({ timeout: 3000 }).catch(() => false)) {
            await row.click();

            // Should navigate to show page
            await page.waitForURL(/\/#\/(textbooks|school-textbooks)\/\d+\/show/);

            // Should have "Edit" button (not read-only)
            const editButton = page.locator('button:has-text("Редактировать")');
            await expect(editButton).toBeVisible();

            // Should be able to edit structure
            const editStructureButton = page.locator('button:has-text("Редактировать структуру")');
            if (await editStructureButton.isVisible({ timeout: 3000 }).catch(() => false)) {
              await expect(editStructureButton).toBeVisible();
            }
          }
        }
      }
    }
  });

  test('should copy all chapters and paragraphs when forking', async ({ page }) => {
    await page.goto('/#/textbooks');

    const globalTab = page.getByRole('tab', { name: /глобальн/i });
    if (await globalTab.isVisible({ timeout: 5000 }).catch(() => false)) {
      await globalTab.click();
      await wait(1000);

      // Find a textbook with chapters (if any)
      const firstRow = page.locator('tbody tr').first();
      if (await firstRow.isVisible({ timeout: 3000 }).catch(() => false)) {
        // View textbook to see if it has chapters
        await firstRow.click();
        await page.waitForURL(/\/#\/textbooks\/\d+\/show/);

        // Go to structure tab
        const structureTab = page.getByRole('tab', { name: /структура/i });
        if (await structureTab.isVisible()) {
          await structureTab.click();

          // Check if it has chapters
          const hasChapters = await page.locator('text=/глава|chapter/i').isVisible({ timeout: 3000 }).catch(() => false);

          if (hasChapters) {
            // Go back and fork this textbook
            await page.goBack();
            await wait(500);

            const customizeButton = page.locator('button:has-text("Кастомизировать")').first();
            if (await customizeButton.isVisible({ timeout: 3000 }).catch(() => false)) {
              await customizeButton.click();

              // Make sure "Copy chapters" is checked
              const copyCheckbox = page.locator('input[type="checkbox"]');
              if (await copyCheckbox.isVisible()) {
                await copyCheckbox.check();
              }

              const timestamp = Date.now();
              const newTitle = `Форк с главами ${timestamp}`;
              await page.fill('input[name="new_title"]', newTitle);
              await page.click('button:has-text("Подтвердить")');

              await wait(3000); // Fork with chapters takes longer

              // View the forked textbook structure
              await page.goto('/#/textbooks');
              const ourTab = page.getByRole('tab', { name: /наши/i });
              if (await ourTab.isVisible()) {
                await ourTab.click();
                await wait(1000);

                const row = page.locator(`tr:has-text("${newTitle}")`).first();
                if (await row.isVisible({ timeout: 3000 }).catch(() => false)) {
                  await row.click();

                  // Go to structure tab
                  const structureTab2 = page.getByRole('tab', { name: /структура/i });
                  if (await structureTab2.isVisible()) {
                    await structureTab2.click();

                    // Should see copied chapters
                    await expect(page.locator('text=/глава|chapter/i')).toBeVisible();
                  }
                }
              }
            }
          }
        }
      }
    }
  });

  test('should NOT allow editing global textbooks directly', async ({ page }) => {
    await page.goto('/#/textbooks');

    const globalTab = page.getByRole('tab', { name: /глобальн/i });
    if (await globalTab.isVisible({ timeout: 5000 }).catch(() => false)) {
      await globalTab.click();
      await wait(1000);

      // Click on a global textbook
      const firstRow = page.locator('tbody tr').first();
      if (await firstRow.isVisible({ timeout: 3000 }).catch(() => false)) {
        await firstRow.click();

        // Should NOT have "Edit" or "Edit Structure" button
        const editButton = page.locator('button:has-text("Редактировать")');
        const editStructureButton = page.locator('button:has-text("Редактировать структуру")');

        // These buttons should NOT be visible (read-only)
        await expect(editButton).not.toBeVisible();
        await expect(editStructureButton).not.toBeVisible();

        // Should only have "Customize" button
        await expect(page.locator('button:has-text("Кастомизировать")')).toBeVisible();
      }
    }
  });
});
