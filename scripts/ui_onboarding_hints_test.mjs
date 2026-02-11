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
    userSystemHint = "Long-press this chat bubble to log in.";
    assistantFallbackText = "Welcome \u2014 I'm Little Chef.\n\nLong-press the system bubble below to sign in.";
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

/**
 * Replicate renderOnboardMenuButtons() login-gate logic.
 * Returns array of button labels the menu would render.
 */
function onboardMenuItems(tokenTrimmed, onboarded, inventoryOnboarded) {
  if (!tokenTrimmed) return ["Login"];
  const items = ["Preferences"];
  if (onboarded) items.push("Inventory");
  if (inventoryOnboarded) items.push("Meal Plan");
  return items;
}

/**
 * Replicate isDebugEnabled() + renderFlowMenu() Dev Panel gating.
 */
function gearMenuIncludesDevPanel(debugEnabled) {
  return debugEnabled;
}

// ---- refreshSystemHints tests ----

// Test: not logged in
{
  const r = refreshSystemHints({ is_logged_in: false, prefs_complete: false, inventory_complete: false, mealplan_complete: false });
  assert(r.assistantFallbackText.includes("sign in"), "not logged in: assistant should mention sign in");
  assert(!r.assistantFallbackText.includes("start onboarding"), "not logged in: should NOT show onboarding prompt");
  assert(r.userSystemHint.includes("Long-press"), "not logged in: user hint should mention Long-press");
  assert(r.userSystemHint.includes("log in"), "not logged in: user hint should mention log in");
}
console.log("not logged in: PASS");

// Test: logged in, prefs NOT complete
{
  const r = refreshSystemHints({ is_logged_in: true, prefs_complete: false, inventory_complete: false, mealplan_complete: false });
  assert(r.assistantFallbackText.includes("start onboarding"), "prefs incomplete: should show onboarding prompt");
  assert(r.userSystemHint.includes("Preferences"), "prefs incomplete: hint should mention Preferences");
}
console.log("logged in, prefs incomplete: PASS");

// Test: logged in, prefs complete, inventory NOT complete
{
  const r = refreshSystemHints({ is_logged_in: true, prefs_complete: true, inventory_complete: false, mealplan_complete: false });
  assert(!r.assistantFallbackText.includes("start onboarding"), "prefs done: should NOT show start onboarding");
  assert(r.assistantFallbackText.includes("Inventory"), "prefs done: should guide to inventory");
  assert(r.userSystemHint.includes("Inventory"), "prefs done: hint should mention Inventory");
}
console.log("logged in, prefs complete, inventory incomplete: PASS");

// Test: logged in, prefs+inventory complete, mealplan NOT complete
{
  const r = refreshSystemHints({ is_logged_in: true, prefs_complete: true, inventory_complete: true, mealplan_complete: false });
  assert(!r.assistantFallbackText.includes("start onboarding"), "inventory done: should NOT show start onboarding");
  assert(!r.assistantFallbackText.includes("set up your inventory"), "inventory done: should NOT guide to inventory");
  assert(r.assistantFallbackText.includes("Meal Plan"), "inventory done: should guide to Meal Plan");
  assert(r.userSystemHint.includes("Meal Plan"), "inventory done: hint should mention Meal Plan");
}
console.log("logged in, prefs+inventory complete, mealplan incomplete: PASS");

// Test: all complete
{
  const r = refreshSystemHints({ is_logged_in: true, prefs_complete: true, inventory_complete: true, mealplan_complete: true });
  assert(!r.assistantFallbackText.includes("start onboarding"), "all done: no onboarding prompt");
  assert(!r.assistantFallbackText.includes("Preferences"), "all done: no prefs guidance in assistant");
  assert(r.assistantFallbackText.includes("all set up"), "all done: should confirm setup complete");
  assert(r.userSystemHint.includes("switch flows"), "all done: hint should offer flow switching");
}
console.log("all onboarding complete: PASS");

// Test: prefs complete + logged in does NOT show preferences onboarding
{
  const r = refreshSystemHints({ is_logged_in: true, prefs_complete: true, inventory_complete: false, mealplan_complete: false });
  assert(!r.assistantFallbackText.includes("To start onboarding"), "prefs done: MUST NOT show 'To start onboarding'");
  assert(!r.userSystemHint.includes("Preferences"), "prefs done: hint MUST NOT mention Preferences");
}
console.log("prefs complete does not show prefs onboarding: PASS");

// Test: after login state transition (simulated)
{
  const before = refreshSystemHints({ is_logged_in: false, prefs_complete: false, inventory_complete: false, mealplan_complete: false });
  assert(before.assistantFallbackText.includes("sign in"), "before login: sign in prompt");

  const after = refreshSystemHints({ is_logged_in: true, prefs_complete: true, inventory_complete: true, mealplan_complete: false });
  assert(!after.assistantFallbackText.includes("sign in"), "after login: no sign in prompt");
  assert(after.assistantFallbackText.includes("Meal Plan"), "after login: guides to meal plan");
}
console.log("login state transition updates messages: PASS");

// ---- onboard menu tests ----

// Test: not logged in -> only Login button
{
  const items = onboardMenuItems(false, false, false);
  assert.deepStrictEqual(items, ["Login"], "not logged in: onboard menu should show only Login");
}
console.log("onboard menu not logged in: PASS");

// Test: logged in, not onboarded -> only Preferences
{
  const items = onboardMenuItems(true, false, false);
  assert.deepStrictEqual(items, ["Preferences"], "logged in, not onboarded: only Preferences");
}
console.log("onboard menu logged in, not onboarded: PASS");

// Test: logged in, prefs onboarded -> Preferences + Inventory
{
  const items = onboardMenuItems(true, true, false);
  assert.deepStrictEqual(items, ["Preferences", "Inventory"], "prefs onboarded: Preferences + Inventory");
}
console.log("onboard menu prefs onboarded: PASS");

// Test: logged in, all onboarded -> Preferences + Inventory + Meal Plan
{
  const items = onboardMenuItems(true, true, true);
  assert.deepStrictEqual(items, ["Preferences", "Inventory", "Meal Plan"], "all onboarded: all three items");
}
console.log("onboard menu all onboarded: PASS");

// ---- debug gate tests ----

// Test: debug disabled -> no Dev Panel in gear menu
{
  assert(!gearMenuIncludesDevPanel(false), "debug off: no Dev Panel");
}
console.log("debug disabled, no Dev Panel: PASS");

// Test: debug enabled -> Dev Panel in gear menu
{
  assert(gearMenuIncludesDevPanel(true), "debug on: Dev Panel present");
}
console.log("debug enabled, Dev Panel present: PASS");

console.log("\nui onboarding hints test: PASS");
