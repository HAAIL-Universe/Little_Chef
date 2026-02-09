import assert from "node:assert";
import { formatProposalSummary, stripProposalPrefix, detectProposalCommand } from "../web/dist/proposalRenderer.js";

const sampleResponse = {
  confirmation_required: true,
  proposed_actions: [
    {
      action_type: "upsert_prefs",
      prefs: {
        allergies: ["peanuts", "shellfish"],
        dislikes: ["mushrooms", "olives"],
        cuisine_likes: ["chicken", "salmon"],
        servings: 2,
        meals_per_day: 2,
        plan_days: 5,
        notes: "No blue cheese",
      },
    },
  ],
};

// Prefs proposals should return null — the canonical summary is now in reply_text (wizard rolling summary).
const summary = formatProposalSummary(sampleResponse);
assert(
  summary === null,
  "formatProposalSummary should return null for prefs-only proposals (wizard reply_text is canonical)"
);
console.log("prefs proposal returns null: PASS");

const inventoryResponse = {
  confirmation_required: true,
  proposed_actions: [
    {
      action_type: "create_inventory_event",
      event: {
        event_type: "add",
        item_name: "cheddar",
        quantity: 1,
        unit: "count",
        note: "weight_g=300",
        source: "chat",
      },
    },
  ],
};
const inventorySummary = formatProposalSummary(inventoryResponse);
assert(
  inventorySummary && inventorySummary.startsWith("Proposed inventory update"),
  "inventory summary should use inventory prefix"
);
assert(
  !inventorySummary.includes("Proposed preferences"),
  "inventory summary should not mention preferences"
);
assert(
  inventorySummary.includes("• Cheddar 1"),
  "inventory summary should describe the item name and quantity"
);
assert(
  !inventorySummary.includes("weight_g="),
  "inventory summary should not surface backend measurement notes"
);

const RealDate = Date;
const frozenDate = new RealDate("2026-02-08T00:00:00Z");
class FrozenDate extends RealDate {
  constructor(...args) {
    if (args.length === 0) {
      return new RealDate(frozenDate);
    }
    return new RealDate(...args);
  }
  static now() {
    return frozenDate.getTime();
  }
  static parse(...args) {
    return RealDate.parse(...args);
  }
  static UTC(...args) {
    return RealDate.UTC(...args);
  }
}

globalThis.Date = FrozenDate;
try {
  const useByResponse = {
    confirmation_required: true,
    proposed_actions: [
      {
        action_type: "create_inventory_event",
        event: {
          event_type: "add",
          item_name: "olive oil",
          quantity: 500,
          unit: "ml",
          note: "weight_g=1200; use_by=9th",
          source: "chat",
        },
      },
    ],
  };
  const useBySummary = formatProposalSummary(useByResponse);
  assert(useBySummary, "use_by summary should exist");
  assert(
    useBySummary.includes("USE BY: 09/02"),
    "inventory summary should render USE BY with fixed month/day format"
  );
  assert(
    !useBySummary.includes("weight_g="),
    "measurements should remain hidden even when use_by is present"
  );

  const useBySecondResponse = {
    confirmation_required: true,
    proposed_actions: [
      {
        action_type: "create_inventory_event",
        event: {
          event_type: "add",
          item_name: "tins chopped tomatoes",
          quantity: 4,
          unit: "count",
          note: "volume_ml=2000; use_by=11th",
          source: "chat",
        },
      },
    ],
  };
  const useBySecondSummary = formatProposalSummary(useBySecondResponse);
  assert(
    useBySecondSummary && useBySecondSummary.includes("USE BY: 11/02"),
    "second use_by entry should show updated day"
  );

  const useByInvalidResponse = {
    confirmation_required: true,
    proposed_actions: [
      {
        action_type: "create_inventory_event",
        event: {
          event_type: "add",
          item_name: "frozen peas",
          quantity: 900,
          unit: "g",
          note: "use_by=??",
          source: "chat",
        },
      },
    ],
  };
  const useByInvalidSummary = formatProposalSummary(useByInvalidResponse);
  assert(
    useByInvalidSummary && !useByInvalidSummary.includes("USE BY:"),
    "invalid use_by tokens should not render"
  );
} finally {
  globalThis.Date = RealDate;
}
const inventoryReply = "Proposed inventory update\n\ninventory update text";
const inventoryCleaned = stripProposalPrefix(inventoryReply);
assert(
  !inventoryCleaned.startsWith("Proposed inventory update"),
  "inventory prefix should be stripped"
);

const rawReply =
  "- Allergies: peanuts, shellfish\n- Dislikes: mushrooms, olives\n- Likes: chicken, salmon\n- Servings: 2\n- Plan days: 5\nReply 'confirm' to save, or send changes to edit.";
// Since formatProposalSummary returns null for prefs proposals,
// the UI will use reply_text directly as the sole summary display.
const prefsProposalSummary = formatProposalSummary(sampleResponse);
assert(prefsProposalSummary === null, "prefs summary is null — reply_text is canonical");
// Simulate UI logic: assistantText = proposalSummary ? ... : replyBase
const assistantText = prefsProposalSummary ? `${prefsProposalSummary}\n\n${rawReply}` : rawReply;
assert(assistantText === rawReply, "display should be exactly the reply_text (no legacy prepend)");
assert(!assistantText.includes("Cuisine likes"), "legacy 'Cuisine likes' label must not appear");
assert(!assistantText.includes("•"), "legacy bullet format must not appear");
assert(assistantText.includes("- Allergies:"), "wizard summary uses hyphen format");
assert(assistantText.includes("Reply 'confirm'"), "confirm instruction present");
console.log("no-duplicate prefs display: PASS");
// --- date= format tests (new-style DD Month dates from parser) ---
const dateResponse = {
  confirmation_required: true,
  proposed_actions: [
    {
      action_type: "create_inventory_event",
      event: {
        event_type: "add",
        item_name: "chopped tomatoes",
        quantity: 8,
        unit: "count",
        note: "date=12 October",
        source: "chat",
      },
    },
    {
      action_type: "create_inventory_event",
      event: {
        event_type: "add",
        item_name: "milk",
        quantity: 2000,
        unit: "ml",
        note: "volume_ml=2000; date=10 February; remaining=1000ml",
        source: "chat",
      },
    },
    {
      action_type: "create_inventory_event",
      event: {
        event_type: "add",
        item_name: "pasta",
        quantity: 3,
        unit: "count",
        note: "weight_g=500",
        source: "chat",
      },
    },
  ],
};
const dateSummary = formatProposalSummary(dateResponse);
assert(dateSummary, "date summary should exist");
assert(
  dateSummary.includes("Chopped Tomatoes 8 (12 October)"),
  `chopped tomatoes should show date, got: ${dateSummary}`
);
assert(
  dateSummary.includes("Milk 2 L (10 February)"),
  `milk should show date, got: ${dateSummary}`
);
assert(
  !dateSummary.includes("Pasta") || !dateSummary.match(/Pasta 3 \(/),
  "pasta without date should not show parenthesised suffix"
);
assert(
  !dateSummary.includes("weight_g=") && !dateSummary.includes("volume_ml="),
  "backend measurement notes should not surface"
);
console.log("date= format tests: PASS");

console.log("ui proposal renderer test: PASS");

const commands = [
  { input: "confirm", expected: "confirm" },
  { input: " Confirm ", expected: "confirm" },
  { input: "CANcel", expected: "deny" },
  { input: "no thanks", expected: null },
];
commands.forEach(({ input, expected }) => {
  const actual = detectProposalCommand(input);
  assert.strictEqual(actual, expected, `detectProposalCommand(${JSON.stringify(input)}) => ${JSON.stringify(actual)}, expected ${JSON.stringify(expected)}`);
});
