const formatList = (label, values) => {
    if (!values || !values.length) {
        return null;
    }
    return `${label}: ${values.join(", ")}`;
};
const describePrefs = (prefs) => {
    const lines = ["Proposed preferences:"];
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
    if (allergyLine)
        lines.push(`- ${allergyLine}`);
    const dislikeLine = formatList("Dislikes", prefs.dislikes);
    if (dislikeLine)
        lines.push(`- ${dislikeLine}`);
    const cuisineLine = formatList("Cuisine likes", prefs.cuisine_likes);
    if (cuisineLine)
        lines.push(`- ${cuisineLine}`);
    if (prefs.notes) {
        lines.push(`- Notes: ${prefs.notes}`);
    }
    return lines;
};
export function formatProposalSummary(response) {
    var _a;
    if (!response || !response.confirmation_required) {
        return null;
    }
    const actions = (_a = response.proposed_actions) !== null && _a !== void 0 ? _a : [];
    const lines = [];
    actions.forEach((action) => {
        if (action.action_type === "upsert_prefs" && action.prefs) {
            lines.push(...describePrefs(action.prefs));
        }
        else {
            lines.push(`Proposal: ${action.action_type}`);
        }
    });
    return lines.length ? lines.join("\n") : null;
}
