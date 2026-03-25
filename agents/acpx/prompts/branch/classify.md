Read the task below.
If it is concrete and scoped, route `continue`.
If it is ambiguous or needs clarification, route `needs_review`.
Return exactly one JSON object with this shape:
{
  "route": "continue" | "needs_review",
  "reason": "short explanation"
}

Task: {{task}}
