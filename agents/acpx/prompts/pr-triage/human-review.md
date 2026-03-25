We are routing this PR to human review.
Return exactly one JSON object with this shape:
{
  "route": "human_review",
  "summary": "short explanation",
  "blocking_reasons": ["reason", "reason"],
  "questions_for_human": ["question", "question"]
}

Runtime reasons: {{reasons}}
