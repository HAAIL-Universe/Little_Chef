const formatList = (label, values) => {
    if (!values || !values.length) {
        return null;
    }
    return `${label}: ${values.join(", ")}`;
};
const describePrefs = (prefs) => {
    const lines = [];
    if (prefs.servings) {
        lines.push(`• Servings: ${prefs.servings}`);
    }
    if (prefs.meals_per_day) {
        lines.push(`• Meals/day: ${prefs.meals_per_day}`);
    }
    if (prefs.days) {
        lines.push(`• Days: ${prefs.days}`);
    }
    const allergyLine = formatList("Allergies", prefs.allergies);
    if (allergyLine)
        lines.push(`• ${allergyLine}`);
    const dislikeLine = formatList("Dislikes", prefs.dislikes);
    if (dislikeLine)
        lines.push(`• ${dislikeLine}`);
    const cuisineLine = formatList("Cuisine likes", prefs.cuisine_likes);
    if (cuisineLine)
        lines.push(`• ${cuisineLine}`);
    if (prefs.notes) {
        lines.push(`• Notes: ${prefs.notes}`);
    }
    return lines;
};
const PROPOSAL_PREFIX_RE = /^Proposed preferences:[^.!?]*(?:[.!?]+)?[\s]*/i;
export function formatProposalSummary(response) {
    var _a;
    if (!response || !response.confirmation_required) {
        return null;
    }
    const actions = (_a = response.proposed_actions) !== null && _a !== void 0 ? _a : [];
    const details = [];
    actions.forEach((action) => {
        if (action.action_type === "upsert_prefs" && action.prefs) {
            details.push(...describePrefs(action.prefs));
        }
        else {
            details.push(`• Proposal: ${action.action_type}`);
        }
    });
    if (!details.length) {
        return null;
    }
    return ["Proposed preferences", "", ...details].join("\n");
}
export function stripProposalPrefix(text) {
    if (!text) {
        return text;
    }
    return text.replace(PROPOSAL_PREFIX_RE, "").trimStart();
}
const PROPOSAL_CONFIRM_COMMANDS = new Set(["confirm"]);
const PROPOSAL_DENY_COMMANDS = new Set(["deny", "cancel"]);
export function detectProposalCommand(message) {
    const normalized = message.trim().toLowerCase();
    if (!normalized)
        return null;
    if (PROPOSAL_CONFIRM_COMMANDS.has(normalized))
        return "confirm";
    if (PROPOSAL_DENY_COMMANDS.has(normalized))
        return "deny";
    return null;
}
