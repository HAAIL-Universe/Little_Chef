import { test, expect } from '@playwright/test';

test.describe('Dev Panel remember row', () => {
  let consoleMessages: string[] = [];

  test.beforeEach(async ({ page }) => {
    consoleMessages = [];
    page.on('console', (message) => consoleMessages.push(`[${message.type()}] ${message.text()}`));
  });

  test.afterEach(async ({ page }, testInfo) => {
    if (testInfo.status !== testInfo.expectedStatus) {
      const logs = consoleMessages.length ? consoleMessages.join('\n') : '(no console messages)';
      await testInfo.attach('browser-console', { body: logs, contentType: 'text/plain' });
      const card = page.locator('section.card.legacy-card:has(#btn-auth)').first();
      if (await card.count()) {
        const html = await card.evaluate((node) => (node as HTMLElement)?.outerHTML ?? '');
        await testInfo.attach('dev-card-html', { body: html, contentType: 'text/html' });
      }
      await testInfo.attach('full-page-screenshot', {
        body: await page.screenshot({ fullPage: true }),
        contentType: 'image/png',
      });
    }
  });

  test('renders remember-me checkbox near the JWT controls', async ({ page }) => {
    await page.goto('/', { waitUntil: 'networkidle' });
    await page.locator('#flow-menu-trigger').click();
    const devPanelItem = page.locator('.flow-menu-dropdown .flow-menu-item', { hasText: 'Dev Panel' });
    await expect(devPanelItem).toBeVisible({ timeout: 10000 });
    await devPanelItem.click();
    const rememberCheckbox = page.locator('#dev-jwt-remember');
    await expect(rememberCheckbox).toBeVisible({ timeout: 15000 });
    const authButton = page.locator('#btn-auth');
    await expect(authButton).toBeVisible({ timeout: 15000 });
    const card = authButton.locator('xpath=ancestor::section[contains(@class,"card")]');
    await expect(card.locator('#dev-jwt-remember')).toHaveCount(1);
  });
});
