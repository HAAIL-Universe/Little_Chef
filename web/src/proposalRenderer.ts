type Prefs = {
  allergies?: string[];
  dislikes?: string[];
  cuisine_likes?: string[];
  servings?: number;
  meals_per_day?: number;
  notes?: string;
  days?: number;
};

type ChatAction = {
  action_type: string;
  prefs?: Prefs;
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
  const lines: string[] = ["Proposed preferences:"];
  if (prefs.servings) {
    lines.push(`- Servings: ${prefs.servings}`);
  }
  if (prefs.meals_per_day) {
    lines.push(`- Meals/day: ${prefs.meals_per_day}`);
  }
  if (prefs.days) {
    lines.push(`- Days: ${prefs.days}`);
  }
  const allergyLine = formatList("Allergies", prefs.allergies);
  if (allergyLine) lines.push(`- ${allergyLine}`);
  const dislikeLine = formatList("Dislikes", prefs.dislikes);
  if (dislikeLine) lines.push(`- ${dislikeLine}`);
  const cuisineLine = formatList("Cuisine likes", prefs.cuisine_likes);
  if (cuisineLine) lines.push(`- ${cuisineLine}`);
  if (prefs.notes) {
    lines.push(`- Notes: ${prefs.notes}`);
  }
  return lines;
};

export function formatProposalSummary(response: ChatResponse | null): string | null {
  if (!response || !response.confirmation_required) {
    return null;
  }
  const actions = response.proposed_actions ?? [];
  const lines: string[] = [];
  actions.forEach((action) => {
    if (action.action_type === "upsert_prefs" && action.prefs) {
      lines.push(...describePrefs(action.prefs));
    } else {
      lines.push(`Proposal: ${action.action_type}`);
    }
  });
  return lines.length ? lines.join("\n") : null;
}
