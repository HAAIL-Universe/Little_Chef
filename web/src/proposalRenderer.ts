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

const formatMealplanAction = (action: ChatAction): string => {
  const mp = action.mealplan;
  if (!mp || !mp.days) {
    return "• Meal plan proposal";
  }
  const dayCount = mp.days.length;
  const mealCount = mp.days.reduce((sum, d) => sum + (d.meals?.length ?? 0), 0);
  const lines: string[] = [`• Meal plan: ${dayCount} day${dayCount !== 1 ? "s" : ""}, ${mealCount} meal${mealCount !== 1 ? "s" : ""}`];
  mp.days.forEach((day) => {
    const names = (day.meals ?? []).map((m) => m.name).join(", ");
    lines.push(`  Day ${day.day_index}: ${names || "(empty)"}`);
  });
  if (mp.notes) {
    lines.push("");
    mp.notes.split("\n").forEach((n) => lines.push(`  ${n}`));
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
