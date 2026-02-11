import { expect, test } from "@playwright/test";

test("proposal actions stack toggles on confirmation_required flow", async ({ page }) => {
  const triggerMessage = "trigger proposal";
  let proposalCounter = 0;
  await page.route("**/chat", async (route, request) => {
    if (request.method() === "POST") {
      const body = JSON.parse(request.postData() ?? "{}");
      if (typeof body.message === "string" && body.message.toLowerCase().includes("trigger")) {
        proposalCounter += 1;
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            reply_text: "Please review the prefs proposal.",
            confirmation_required: true,
            proposal_id: `test-proposal-${proposalCounter}`,
            proposed_actions: [
              {
                action_type: "upsert_prefs",
                prefs: { servings: 3, meals_per_day: 2 },
              },
            ],
            mode: "fill",
            thread_id: body.thread_id,
          }),
        });
        return;
      }
    }
    await route.continue();
  });

  let confirmPayload: any = null;
  await page.route("**/chat/confirm", async (route, request) => {
    confirmPayload = JSON.parse(request.postData() ?? "{}");
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ applied: true, confirmation_required: false }),
    });
  });

  await page.goto("/?skipauth=1", { waitUntil: "networkidle" });

  const input = page.locator("#duet-input");
  const sendBtn = page.locator("#duet-send");
  const actions = page.locator("#proposal-actions");

  await input.fill(triggerMessage);
  await sendBtn.evaluate((btn) => (btn as HTMLButtonElement).click());
  await expect(actions).toHaveClass(/visible/, { timeout: 10000 });
  await expect(actions.locator("button")).toHaveCount(3);

  await page.locator("#proposal-confirm").click();
  await expect(confirmPayload).not.toBeNull();
  expect(confirmPayload?.confirm).toBe(true);
  await expect(actions).not.toHaveClass(/visible/, { timeout: 5000 });

  await input.fill(triggerMessage);
  await sendBtn.evaluate((btn) => (btn as HTMLButtonElement).click());
  await expect(actions).toHaveClass(/visible/, { timeout: 10000 });
  await page.locator("#proposal-deny").click();
  await expect(actions).not.toHaveClass(/visible/, { timeout: 5000 });
});
