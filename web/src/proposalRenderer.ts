type Prefs = {
  allergies?: string[];
  dislikes?: string[];
  cuisine_likes?: string[];
  servings?: number;
  meals_per_day?: number;
  plan_days?: number;
  notes?: string;
};

type InventoryEvent = {
  event_type: string;
  item_name: string;
  quantity: number;
  unit: string;
  note?: string;
};

type PlannedMeal = {
  name: string;
  slot: string;
  ingredients?: Array<{ item_name?: string }>;
};

type MealPlanDay = {
  day_index: number;
  meals: PlannedMeal[];
};

type MealPlanData = {
  plan_id?: string;
  days: MealPlanDay[];
  notes?: string;
};

type ChatAction = {
  action_type: string;
  prefs?: Prefs;
  event?: InventoryEvent;
  mealplan?: MealPlanData;
};

type ChatResponse = {
  confirmation_required?: boolean;
  proposed_actions?: ChatAction[];
};

const formatList = (label: string, values?: string[] | null): string | null => {
  if (!values || !values.length) {
    return null;
  }
  return `${label}: ${values.join(", ")}`;
};

const describePrefs = (prefs: Prefs): string[] => {
  const lines: string[] = [];
  if (prefs.servings) {
    lines.push(`• Servings: ${prefs.servings}`);
  }
  if (prefs.meals_per_day) {
    lines.push(`• Meals/day: ${prefs.meals_per_day}`);
  }
  if (prefs.plan_days) {
    lines.push(`• Plan days: ${prefs.plan_days}`);
  }
  const allergyLine = formatList("Allergies", prefs.allergies);
  if (allergyLine) lines.push(`• ${allergyLine}`);
  const dislikeLine = formatList("Dislikes", prefs.dislikes);
  if (dislikeLine) lines.push(`• ${dislikeLine}`);
  const cuisineLine = formatList("Cuisine likes", prefs.cuisine_likes);
  if (cuisineLine) lines.push(`• ${cuisineLine}`);
  if (prefs.notes) {
    lines.push(`• Notes: ${prefs.notes}`);
  }
  return lines;
};

const parseNoteKeyValues = (note: string): Record<string, string> => {
  const fields: Record<string, string> = {};
  note.split(";").forEach((piece) => {
    const trimmed = piece.trim();
    if (!trimmed) {
      return;
    }
    const equalsIndex = trimmed.indexOf("=");
    if (equalsIndex < 0) {
      return;
    }
    const key = trimmed.slice(0, equalsIndex).trim().toLowerCase();
    const value = trimmed.slice(equalsIndex + 1).trim();
    if (!key || !value) {
      return;
    }
    fields[key] = value;
  });
  return fields;
};

const formatUseByToken = (value?: string): string | null => {
  if (!value) {
    return null;
  }
  const digits = value.replace(/\D/g, "");
  if (!digits) {
    return null;
  }
  const dayNum = parseInt(digits, 10);
  if (Number.isNaN(dayNum) || dayNum < 1 || dayNum > 31) {
    return null;
  }
  const now = new Date();
  const month = now.getMonth() + 1;
  const dayText = String(dayNum).padStart(2, "0");
  const monthText = String(month).padStart(2, "0");
  return `USE BY: ${dayText}/${monthText}`;
};

const splitSectionItems = (text: string): string[] => {
  const normalized = text.trim().replace(/\s+/g, " ");
  if (!normalized) return [];
  const byLine = normalized
    .split(/\r?\n/)
    .map((line) => line.trim().replace(/^[,.;:]+\s*/, "").replace(/[.;:]+$/, ""))
    .filter(Boolean);
  if (byLine.length > 1) {
    return byLine;
  }
  // Backend currently emits comma-separated items in notes sections.
  return normalized
    .split(/\s*,\s*/)
    .map((item) => item.trim().replace(/^[,.;:]+\s*/, "").replace(/[.;:]+$/, ""))
    .filter(Boolean);
};

const splitNeededItems = (text: string): string[] => {
  const normalized = text.trim();
  if (!normalized) return [];
  const byLine = normalized
    .split(/\r?\n/)
    .map((line) => line.trim().replace(/^[,.;:]+\s*/, "").replace(/[.;:]+$/, ""))
    .filter(Boolean);
  if (byLine.length > 1) {
    return byLine;
  }
  // Backend format: "name (qty unit), name (qty unit)"
  const qtyMatches = normalized.match(/[^,]+?\([^)]*\)(?=,\s*|$)/g);
  if (qtyMatches && qtyMatches.length) {
    return qtyMatches
      .map((item) => item.trim().replace(/^[,.;:]+\s*/, "").replace(/[.;:]+$/, ""))
      .filter(Boolean);
  }
  return splitSectionItems(normalized);
};

const parseMealplanNotes = (notes?: string) => {
  const result = {
    have: "",
    need: "",
    cookTime: "",
    extras: [] as string[],
  };
  if (!notes) {
    return result;
  }

  const sectionMarkers: Array<{ name: string; start: number; end: number }> = [];
  const sectionRegex = /(You have|You need|Cook time prefs):/gi;
  let sectionMatch: RegExpExecArray | null = null;
  while ((sectionMatch = sectionRegex.exec(notes)) !== null) {
    sectionMarkers.push({
      name: sectionMatch[1].toLowerCase(),
      start: sectionMatch.index,
      end: sectionMatch.index + sectionMatch[0].length,
    });
  }

  if (!sectionMarkers.length) {
    result.extras = notes
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter(Boolean);
    return result;
  }

  for (let i = 0; i < sectionMarkers.length; i++) {
    const marker = sectionMarkers[i];
    const nextStart = sectionMarkers[i + 1]?.start ?? notes.length;
    const raw = notes
      .slice(marker.end, nextStart)
      .trim()
      .replace(/^[\s:.-]+/, "")
      .replace(/[.\s]+$/, "")
      .trim();
    if (!raw) continue;
    if (marker.name === "you have") {
      result.have = raw;
      continue;
    }
    if (marker.name === "you need") {
      result.need = raw;
      continue;
    }
    if (marker.name === "cook time prefs") {
      result.cookTime = raw;
    }
  }
  return result;
};

const formatMealplanAction = (action: ChatAction): string => {
  const mp = action.mealplan;
  if (!mp || !mp.days) {
    return "• Meal plan proposal";
  }
  const dayCount = mp.days.length;
  const mealCount = mp.days.reduce((sum, d) => sum + (d.meals?.length ?? 0), 0);
  const lines: string[] = [`• Meal plan: ${dayCount} day${dayCount !== 1 ? "s" : ""}, ${mealCount} meal${mealCount !== 1 ? "s" : ""}`];

  const ingredientNames = new Map<string, string>();
  mp.days.forEach((day) => {
    lines.push(`  Day ${day.day_index}`);
    const meals = day.meals ?? [];
    if (!meals.length) {
      lines.push("    • (empty)");
      return;
    }
    meals.forEach((meal) => {
      lines.push(`    • ${meal.slot}: ${meal.name}`);
      (meal.ingredients ?? []).forEach((ingredient) => {
        const name = (ingredient.item_name ?? "").trim();
        if (!name) return;
        const key = name.toLowerCase();
        if (!ingredientNames.has(key)) {
          ingredientNames.set(key, name);
        }
      });
    });
  });
  if (mp.notes) {
    const parsed = parseMealplanNotes(mp.notes);
    const neededItems = splitNeededItems(parsed.need);
    const neededNames = new Set(
      neededItems
        .map((item) => item.replace(/\s*\([^)]*\)\s*$/, "").trim().toLowerCase())
        .filter(Boolean)
    );
    const derivedHave = Array.from(ingredientNames.entries())
      .filter(([key]) => !neededNames.has(key))
      .map(([, original]) => original)
      .sort((a, b) => a.localeCompare(b));
    const haveItems = derivedHave.length ? derivedHave : splitSectionItems(parsed.have);

    lines.push("");
    if (neededItems.length) {
      lines.push("  You need");
      neededItems.forEach((item) => lines.push(`    • ${item}`));
    }
    if (haveItems.length) {
      if (neededItems.length) {
        lines.push("");
      }
      lines.push("  You have");
      haveItems.forEach((item) => lines.push(`    • ${item}`));
    }
    if (parsed.cookTime) {
      lines.push("");
      lines.push(`  Cook time prefs: ${parsed.cookTime}`);
    }
    if (parsed.extras.length) {
      if (haveItems.length || neededItems.length || parsed.cookTime) {
        lines.push("");
      }
      parsed.extras.forEach((extra) => lines.push(`  ${extra}`));
    }
  }
  return lines.join("\n");
};

const formatInventoryAction = (action: ChatAction): string => {
  const event = action.event;
  if (!event) {
    return `• Proposal: ${action.action_type}`;
  }

  const titleName = event.item_name.replace(/\b\w/g, (c) => c.toUpperCase());
  const components: string[] = [titleName];

  // Quantity formatting (hide "count", humanize g/ml when sensible)
  if (event.quantity !== undefined && event.quantity !== null) {
    const unit = (event.unit || "").trim().toLowerCase();

    let qtyText = "";

    if (!unit || unit === "count") {
      qtyText = `${event.quantity}`;
    } else if (
      unit === "g" &&
      typeof event.quantity === "number" &&
      event.quantity >= 1000 &&
      event.quantity % 1000 === 0
    ) {
      qtyText = `${event.quantity / 1000} kg`;
    } else if (
      unit === "ml" &&
      typeof event.quantity === "number" &&
      event.quantity >= 1000 &&
      event.quantity % 1000 === 0
    ) {
      qtyText = `${event.quantity / 1000} L`;
    } else {
      qtyText = `${event.quantity} ${unit}`;
    }

    components.push(qtyText);
  }

  if (event.note) {
    const noteFields = parseNoteKeyValues(event.note);

    // Show date from "date=DD Month" (covers use-by and best-before)
    if (noteFields["date"]) {
      components.push(`(${noteFields["date"]})`);
    } else {
      // Legacy fallback: bare use_by day number
      const useByToken = formatUseByToken(noteFields["use_by"]);
      if (useByToken) {
        components.push(useByToken);
      }
    }
  }

  return `• ${components.join(" ")}`;
};

export function formatProposalSummary(response: ChatResponse | null): string | null {
  if (!response || !response.confirmation_required) {
    return null;
  }
  const actions = response.proposed_actions ?? [];
  const details: string[] = [];
  actions.forEach((action) => {
    if (action.action_type === "upsert_prefs") {
      // Prefs summary is canonical in reply_text (wizard rolling summary);
      // skip legacy describePrefs to avoid duplicate display.
      return;
    }
    if (action.action_type === "generate_mealplan") {
      details.push(formatMealplanAction(action));
      return;
    }
    details.push(formatInventoryAction(action));
  });
  if (!details.length) {
    return null;
  }
  const allInventory = actions.every((action) => action.action_type === "create_inventory_event");
  const hasMealplan = actions.some((action) => action.action_type === "generate_mealplan");
  const hasPrefs = actions.some((action) => action.action_type === "upsert_prefs");
  let prefix = "Proposed update";
  if (hasMealplan) {
    prefix = "Proposed meal plan";
  } else if (allInventory) {
    prefix = "Proposed inventory update";
  } else if (hasPrefs) {
    prefix = "Proposed preferences";
  }
  return [prefix, "", ...details].join("\n");
}

export function stripProposalPrefix(text: string | null): string | null {
  if (!text) {
    return text;
  }
  const trimmed = text.trimStart();
  const prefixLength = text.length - trimmed.length;
  if (!trimmed.toLowerCase().startsWith("proposed ")) {
    return trimmed;
  }
  let rest = text.slice(prefixLength);
  const newlineIdx = rest.indexOf("\n");
  if (newlineIdx >= 0) {
    rest = rest.slice(newlineIdx + 1);
  } else {
    const periodIdx = rest.indexOf(".");
    if (periodIdx >= 0) {
      rest = rest.slice(periodIdx + 1);
    } else {
      rest = "";
    }
  }
  rest = rest.replace(/^\s*(\r?\n)*/, "");
  return rest.trimStart();
}

const PROPOSAL_CONFIRM_COMMANDS = new Set(["confirm"]);
const PROPOSAL_DENY_COMMANDS = new Set(["deny", "cancel"]);

export type ProposalCommand = "confirm" | "deny";

export function detectProposalCommand(message: string): ProposalCommand | null {
  const normalized = message.trim().toLowerCase();
  if (!normalized) return null;
  if (PROPOSAL_CONFIRM_COMMANDS.has(normalized)) return "confirm";
  if (PROPOSAL_DENY_COMMANDS.has(normalized)) return "deny";
  return null;
}
