import { expect, test } from "@playwright/test";

test("inventory overlay appears after confirming inventory proposal", async ({ page }) => {
  const triggerMessage = "trigger inventory";
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
            reply_text: "Please review the inventory proposal.",
            confirmation_required: true,
            proposal_id: `test-inv-proposal-${proposalCounter}`,
            proposed_actions: [
              {
                action_type: "create_inventory_event",
                event: { event_type: "add", item_name: "Tomato", quantity: 3, unit: "pcs" },
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

  // inventory flow posts to /chat/inventory
  await page.route("**/chat/inventory", async (route, request) => {
    if (request.method() === "POST") {
      const body = JSON.parse(request.postData() ?? "{}");
      if (typeof body.message === "string" && body.message.toLowerCase().includes("trigger")) {
        proposalCounter += 1;
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            reply_text: "Please review the inventory proposal.",
            confirmation_required: true,
            proposal_id: `test-inv-proposal-${proposalCounter}`,
            proposed_actions: [
              {
                action_type: "create_inventory_event",
                event: { event_type: "add", item_name: "Tomato", quantity: 3, unit: "pcs" },
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

  await page.route("**/inventory/summary", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ items: [{ item_name: "Tomato", quantity: 3, unit: "pcs" }] }),
    });
  });

  await page.route("**/inventory/low-stock", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ items: [] }),
    });
  });

  await page.goto("/?skipauth=1", { waitUntil: "networkidle" });

  // Select Inventory flow
  const trigger = page.locator("#flow-menu-trigger");
  if (await trigger.isVisible()) {
    await trigger.click();
    const inventoryItem = page.locator(".flow-menu-item").filter({ hasText: "Inventory" });
    await inventoryItem.click();
    await expect(page.locator("#duet-flow-chip")).toHaveText("[Inventory]", { timeout: 5000 });
  }

  const input = page.locator("#duet-input");
  const sendBtn = page.locator("#duet-send");
  const actions = page.locator("#proposal-actions");

  await input.fill(triggerMessage);
  await sendBtn.evaluate((btn) => (btn as HTMLButtonElement).click());
  await expect(actions).toHaveClass(/visible/, { timeout: 10000 });

  await page.locator("#proposal-confirm").click();
  await expect(confirmPayload).not.toBeNull();
  expect(confirmPayload?.confirm).toBe(true);

  // After confirm, inventory overlay should be visible and show the Tomato item
  const overlay = page.locator("#inventory-ghost");
  await expect(overlay).toBeVisible({ timeout: 10000 });
  await expect(page.locator("#inventory-summary-list li").filter({ hasText: "Tomato" })).toHaveCount(1);

  // The user bubble is hidden in inventory flow by design; make it visible
  // so we can long-press it to verify the onboard menu contents.
  const bubble = page.locator("#duet-user-bubble");
  await page.evaluate(() => {
    const el = document.getElementById("duet-user-bubble");
    if (el) el.style.display = "";
  });
  await expect(bubble).toBeVisible({ timeout: 3000 });
  const box = await bubble.boundingBox();
  if (!box) throw new Error("User bubble is not visible for long press");
  const centerX = box.x + box.width / 2;
  const centerY = box.y + box.height / 2;
  await page.mouse.move(centerX, centerY);
  await page.mouse.down();
  await page.waitForTimeout(650);
  await page.mouse.up();

  // After long-press the onboard menu should appear; check Meal Plan entry
  const onboardMenu = page.locator("#onboard-menu");
  await expect(onboardMenu).toBeVisible({ timeout: 3000 });
  const mealPlanBtn = onboardMenu.locator("button[data-onboard-item=mealplan]");
  await expect(mealPlanBtn).toHaveCount(1);
  await expect(mealPlanBtn).not.toHaveClass(/hidden/);
});
