import assert from "node:assert";
import { formatProposalSummary } from "../web/dist/proposalRenderer.js";

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
console.log("ui proposal renderer test: PASS");
