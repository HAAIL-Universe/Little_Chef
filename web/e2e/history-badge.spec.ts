import { expect, test } from "@playwright/test";

test.describe("History badge and bubble", () => {
  test("sent bubble and badge track normal chat activity", async ({ page }) => {
    await page.goto("/?skipauth=1", { waitUntil: "networkidle" });
    const bubbleText = page.locator("#duet-user-bubble .bubble-text");
    await expect(bubbleText).toBeVisible({ timeout: 15000 });

    const input = page.locator("#duet-input");
    const sendBtn = page.locator("#duet-send");
    const badge = page.locator("#duet-history-toggle .history-badge");
    const historyToggle = page.locator("#duet-history-toggle");
    const historyList = page.locator("#duet-history-list li");
    const historyPanel = page.locator("#duet-history");

    for (let i = 1; i <= 3; i += 1) {
      await input.fill(`message ${i}`);
      await sendBtn.evaluate((btn) => (btn as HTMLButtonElement).click());
      await expect(bubbleText).toHaveText("👍", { timeout: 5000 });
    }

    await expect(badge).toHaveText("3", { timeout: 5000 });
    await expect(badge).toHaveClass(/visible/);

    await historyToggle.click();
    await expect(historyPanel).toHaveClass(/open/, { timeout: 5000 });
    await expect(historyList.filter({ hasText: "[General] message 1" }).first()).toBeVisible({
      timeout: 5000,
    });
    await expect(badge).not.toHaveClass(/visible/);
    await expect(badge).toHaveText("", { timeout: 5000 });

    await historyToggle.click();
    await expect(historyPanel).not.toHaveClass(/open/);

    await input.fill("message 4");
    await sendBtn.evaluate((btn) => (btn as HTMLButtonElement).click());
    await expect(badge).toHaveText("1", { timeout: 5000 });
    await expect(badge).toHaveClass(/visible/, { timeout: 5000 });
    await expect(bubbleText).toHaveText("👍", { timeout: 5000 });
  });
});
