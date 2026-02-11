import assert from "node:assert";

/**
 * Test the onboarding message selection logic from web/src/main.ts.
 *
 * Since main.ts has DOM side-effects and cannot be imported in Node,
 * we replicate the pure refreshSystemHints() logic here and validate
 * that the correct messages are produced for each onboarding state.
 *
 * If the logic in main.ts changes, this test must be updated to match.
 */

const USER_BUBBLE_DEFAULT_HINT = "Long-press this chat bubble to navigate > Preferences";

function refreshSystemHints(status) {
  let userSystemHint;
  let assistantFallbackText;

  if (!status.is_logged_in) {
    userSystemHint = "Enter your JWT token above and tap Auth to sign in.";
    assistantFallbackText = "Welcome \u2014 I'm Little Chef.\n\nPlease sign in to get started.";
  } else if (!status.prefs_complete) {
    userSystemHint = USER_BUBBLE_DEFAULT_HINT;
    assistantFallbackText =
      "Welcome \u2014 I'm Little Chef.\n\nTo start onboarding, follow the instructions below.";
  } else if (!status.inventory_complete) {
    userSystemHint = "Long-press this chat bubble to navigate > Inventory";
    assistantFallbackText =
      "Preferences saved! Next step: set up your inventory.\n\nLong-press the system bubble below to navigate to Inventory.";
  } else if (!status.mealplan_complete) {
    userSystemHint = "Long-press this chat bubble to finish onboarding > Meal Plan";
    assistantFallbackText =
      "Inventory set up! Next step: create your first meal plan.\n\nLong-press the system bubble below to navigate to Meal Plan.";
  } else {
    userSystemHint = "Long-press this chat bubble to switch flows.";
    assistantFallbackText =
      "Welcome back! You're all set up.\n\nUse the flows to manage preferences, inventory, or meal plans.";
  }

  return { userSystemHint, assistantFallbackText };
}

// ---- Test: not logged in ----
{
  const r = refreshSystemHints({ is_logged_in: false, prefs_complete: false, inventory_complete: false, mealplan_complete: false });
  assert(r.assistantFallbackText.includes("sign in"), "not logged in: assistant should mention sign in");
  assert(!r.assistantFallbackText.includes("start onboarding"), "not logged in: should NOT show onboarding prompt");
  assert(r.userSystemHint.includes("Auth"), "not logged in: user hint should mention Auth");
}
console.log("not logged in: PASS");

// ---- Test: logged in, prefs NOT complete ----
{
  const r = refreshSystemHints({ is_logged_in: true, prefs_complete: false, inventory_complete: false, mealplan_complete: false });
  assert(r.assistantFallbackText.includes("start onboarding"), "prefs incomplete: should show onboarding prompt");
  assert(r.userSystemHint.includes("Preferences"), "prefs incomplete: hint should mention Preferences");
}
console.log("logged in, prefs incomplete: PASS");

// ---- Test: logged in, prefs complete, inventory NOT complete ----
{
  const r = refreshSystemHints({ is_logged_in: true, prefs_complete: true, inventory_complete: false, mealplan_complete: false });
  assert(!r.assistantFallbackText.includes("start onboarding"), "prefs done: should NOT show start onboarding");
  assert(r.assistantFallbackText.includes("Inventory"), "prefs done: should guide to inventory");
  assert(r.userSystemHint.includes("Inventory"), "prefs done: hint should mention Inventory");
}
console.log("logged in, prefs complete, inventory incomplete: PASS");

// ---- Test: logged in, prefs+inventory complete, mealplan NOT complete ----
{
  const r = refreshSystemHints({ is_logged_in: true, prefs_complete: true, inventory_complete: true, mealplan_complete: false });
  assert(!r.assistantFallbackText.includes("start onboarding"), "inventory done: should NOT show start onboarding");
  assert(!r.assistantFallbackText.includes("set up your inventory"), "inventory done: should NOT guide to inventory");
  assert(r.assistantFallbackText.includes("Meal Plan"), "inventory done: should guide to Meal Plan");
  assert(r.userSystemHint.includes("Meal Plan"), "inventory done: hint should mention Meal Plan");
}
console.log("logged in, prefs+inventory complete, mealplan incomplete: PASS");

// ---- Test: all complete ----
{
  const r = refreshSystemHints({ is_logged_in: true, prefs_complete: true, inventory_complete: true, mealplan_complete: true });
  assert(!r.assistantFallbackText.includes("start onboarding"), "all done: no onboarding prompt");
  assert(!r.assistantFallbackText.includes("Preferences"), "all done: no prefs guidance in assistant");
  assert(r.assistantFallbackText.includes("all set up"), "all done: should confirm setup complete");
  assert(r.userSystemHint.includes("switch flows"), "all done: hint should offer flow switching");
}
console.log("all onboarding complete: PASS");

// ---- Test: prefs complete + logged in does NOT show preferences onboarding ----
{
  const r = refreshSystemHints({ is_logged_in: true, prefs_complete: true, inventory_complete: false, mealplan_complete: false });
  assert(!r.assistantFallbackText.includes("To start onboarding"), "prefs done: MUST NOT show 'To start onboarding'");
  assert(!r.userSystemHint.includes("Preferences"), "prefs done: hint MUST NOT mention Preferences");
}
console.log("prefs complete does not show prefs onboarding: PASS");

// ---- Test: after login state transition (simulated) ----
{
  // Simulate: start not logged in, then login with prefs+inventory complete
  const before = refreshSystemHints({ is_logged_in: false, prefs_complete: false, inventory_complete: false, mealplan_complete: false });
  assert(before.assistantFallbackText.includes("sign in"), "before login: sign in prompt");

  const after = refreshSystemHints({ is_logged_in: true, prefs_complete: true, inventory_complete: true, mealplan_complete: false });
  assert(!after.assistantFallbackText.includes("sign in"), "after login: no sign in prompt");
  assert(after.assistantFallbackText.includes("Meal Plan"), "after login: guides to meal plan");
}
console.log("login state transition updates messages: PASS");

console.log("\nui onboarding hints test: PASS");
