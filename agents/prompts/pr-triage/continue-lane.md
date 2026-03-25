We are continuing on the autonomous lane.
The runtime routed here because the earlier checks did not raise blockers.
Return exactly one JSON object with this shape:
{
  "route": "continue",
  "summary": "short explanation",
  "next_actions": ["action", "action"],
  "residual_risks": ["risk", "risk"]
}

Runtime reasons: {{reasons}}
