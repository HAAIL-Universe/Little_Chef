import { expect, test } from "@playwright/test";

test.describe("History badge and bubble", () => {
  test("sent bubble and badge track normal chat activity", async ({ page }) => {
    // Mock /chat so sends succeed deterministically without a live backend
    await page.route("**/chat", async (route, request) => {
      if (request.method() === "POST") {
        const body = JSON.parse(request.postData() ?? "{}");
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            reply_text: "ok",
            thread_id: body.thread_id ?? "t1",
          }),
        });
        return;
      }
      await route.continue();
    });

    await page.goto("/?skipauth=1", { waitUntil: "networkidle" });
    const sentIndicator = page.locator("#duet-sent-indicator");

    const input = page.locator("#duet-input");
    const sendBtn = page.locator("#duet-send");
    const badge = page.locator("#duet-history-toggle .history-badge");
    const historyToggle = page.locator("#duet-history-toggle");
    const historyList = page.locator("#duet-history-list li");
    const historyPanel = page.locator("#duet-history");

    for (let i = 1; i <= 3; i += 1) {
      await input.fill(`message ${i}`);
      await sendBtn.evaluate((btn) => (btn as HTMLButtonElement).click());
      await expect(sentIndicator).toHaveText("👍", { timeout: 5000 });
      await expect(sentIndicator).toHaveClass(/visible/, { timeout: 5000 });
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
    await expect(sentIndicator).toHaveText("👍", { timeout: 5000 });
    await expect(sentIndicator).toHaveClass(/visible/, { timeout: 5000 });
  });
});
