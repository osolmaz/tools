You are doing maintainability-first PR triage.
Question: is this the right solution for the underlying issue, or is it only a localized fix that does not address the real problem?
Use only the PR context below.
Return exactly one JSON object with this shape:
{
  "verdict": "right_solution" | "localized_fix" | "wrong_problem" | "unclear",
  "confidence": 0.0,
  "reason": "short explanation",
  "evidence": ["short bullet", "short bullet"]
}

{{promptContext}}
