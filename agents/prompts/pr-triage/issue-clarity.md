Use the PR context already in this session.
Judge whether the underlying issue is clearly framed enough for safe autonomous continuation.
If there is no linked issue, decide whether the PR body still makes the underlying problem clear.
Return exactly one JSON object with this shape:
{
  "verdict": "clear" | "ambiguous" | "conflicting",
  "confidence": 0.0,
  "reason": "short explanation"
}
