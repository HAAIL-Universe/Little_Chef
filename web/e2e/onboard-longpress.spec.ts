import { test, expect } from '@playwright/test';

test.describe('Onboard long-press menu', () => {
  test('opens above the bubble and stays topmost', async ({ page }) => {
    await page.goto('/', { waitUntil: 'networkidle' });
    const bubble = page.locator('#duet-user-bubble');
    await expect(bubble).toBeVisible({ timeout: 15000 });
    const box = await bubble.boundingBox();
    if (!box) {
      throw new Error('User bubble is not visible for long press');
    }
    const centerX = box.x + box.width / 2;
    const centerY = box.y + box.height / 2;
    await page.mouse.move(centerX, centerY);
    await page.mouse.down();
    await page.waitForTimeout(650);
    await page.mouse.up();

    const menu = page.locator('#onboard-menu');
    await expect(menu).toBeVisible({ timeout: 5000 });
    const menuRect = await menu.boundingBox();
    if (!menuRect) {
      throw new Error('Onboard menu did not render a bounding box');
    }

    const topmostResult = await page.evaluate(() => {
      const menuEl = document.getElementById('onboard-menu');
      if (!menuEl) {
        return { isTopmost: false, id: "", className: "", tag: "" };
      }
      const rect = menuEl.getBoundingClientRect();
      const pointX = rect.left + rect.width / 2;
      const pointY = rect.top + rect.height / 2;
      const topmost = document.elementFromPoint(pointX, pointY);
      return {
        isTopmost: !!topmost && menuEl.contains(topmost),
        id: topmost?.id ?? "",
        className: topmost?.className ?? "",
        tag: topmost?.tagName ?? "",
      };
    });
    if (!topmostResult.isTopmost) {
      throw new Error(
        `elementFromPoint hit ${topmostResult.tag}#${topmostResult.id} ${topmostResult.className}`
      );
    }
  });
});
