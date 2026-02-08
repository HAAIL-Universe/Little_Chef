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
        notes: "No blue cheese",
      },
    },
  ],
};

const summary = formatProposalSummary(sampleResponse);
assert(summary, "proposal summary should be generated");
assert(summary.includes("Proposed preferences"), "summary heading missing");
assert(summary.includes("Servings: 2"), "servings value missing");
assert(summary.includes("Allergies: peanuts, shellfish"), "allergy list missing");
assert(summary.includes("Dislikes: mushrooms, olives"), "dislikes missing");
assert(summary.includes("Cuisine likes: chicken, salmon"), "cuisine likes missing");
assert(
  summary.indexOf("Proposed preferences") === summary.lastIndexOf("Proposed preferences"),
  "heading should appear only once"
);

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
  inventorySummary.includes("• cheddar 1"),
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
  "Proposed preferences: servings 2, meals/day 2. Reply CONFIRM to save or continue editing.";
const cleaned = stripProposalPrefix(rawReply);
assert(cleaned, "reply text should remain after stripping prefix");
assert(!cleaned.startsWith("Proposed preferences"), "prefix should be removed");
assert(cleaned.includes("Reply CONFIRM"), "confirmation instruction preserved");
const assistantText = `${summary}\n\n${cleaned}`;
const confirmCount = (assistantText.match(/Reply CONFIRM/g) ?? []).length;
const headingCount = (assistantText.match(/Proposed preferences/g) ?? []).length;
assert(confirmCount === 1, "confirmation instruction should appear once");
assert(headingCount === 1, "heading should appear once");
assert(assistantText.startsWith("Proposed preferences"), "heading should appear first");
assert(assistantText.includes("\n• Servings: 2"), "servings line present");
assert(assistantText.includes("\n• Meals/day: 2"), "meals/day line present");
assert(
  assistantText.includes("\n• Allergies:"),
  "allergies bullet on its own line"
);
assert(
  assistantText.indexOf("Reply CONFIRM") > assistantText.indexOf("Proposed preferences"),
  "confirm instruction should appear after the proposal block"
);
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
