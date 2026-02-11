import { expect, test } from "@playwright/test";

test.describe("Flow chip indicator", () => {
  test("shows [General] on initial load", async ({ page }) => {
    await page.goto("/?skipauth=1", { waitUntil: "networkidle" });
    const chip = page.locator("#duet-flow-chip");
    await expect(chip).toBeVisible({ timeout: 15000 });
    await expect(chip).toHaveText("[General]", { timeout: 5000 });
  });

  test("updates to [Inventory] when inventory flow is selected", async ({ page }) => {
    await page.goto("/?skipauth=1", { waitUntil: "networkidle" });
    const chip = page.locator("#duet-flow-chip");
    await expect(chip).toBeVisible({ timeout: 15000 });

    // Open flow menu and select Inventory
    const trigger = page.locator("#flow-menu-trigger");
    if (await trigger.isVisible()) {
      await trigger.click();
      const inventoryItem = page.locator(".flow-menu-item").filter({ hasText: "Inventory" });
      await inventoryItem.click();
      await expect(chip).toHaveText("[Inventory]", { timeout: 5000 });
    }
  });

  test("updates to [Preferences] when prefs flow is selected", async ({ page }) => {
    await page.goto("/?skipauth=1", { waitUntil: "networkidle" });
    const chip = page.locator("#duet-flow-chip");
    await expect(chip).toBeVisible({ timeout: 15000 });

    // Open flow menu and select Preferences
    const trigger = page.locator("#flow-menu-trigger");
    if (await trigger.isVisible()) {
      await trigger.click();
      const prefsItem = page.locator(".flow-menu-item").filter({ hasText: "Preferences" });
      await prefsItem.click();
      await expect(chip).toHaveText("[Preferences]", { timeout: 5000 });
    }
  });
});
