Use the PR context and earlier reasoning already in this session.
Judge whether the scope is appropriately shaped for the codebase.
Return exactly one JSON object with this shape:
{
  "scope": "appropriately_local" | "too_local" | "cross_cutting_needed",
  "refactor_needed": "none" | "superficial" | "fundamental",
  "human_judgment_needed": true | false,
  "reason": "short explanation"
}
