import os
import json
from anthropic import Anthropic
from app.models import AnalyzeResponse

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are a staff software engineer with deep expertise in PostgreSQL. Your job is to analyze the output of an EXPLAIN ANALYZE query plan and identify performance problems.

Look for the following:
- Sequential scans on large tables
- Poor or missing indexing, including cases where rows removed by filter indicates an index would help
- Nested loops with high iteration counts
- Large discrepancies between actual and expected row counts, which may indicate stale statistics or poor planner estimates
- Overall execution time
- Any other significant performance problems you identify

Use the following severity definitions for each finding:
- critical: will result in marked performance degradation or significant infrastructure cost impact
- warning: may have noticeable performance or cost impact, but less severe than critical
- suggestion: worth monitoring as it could become a warning or critical issue as the system scales

overall_severity should reflect the highest severity finding present.

Use the following finding_type values to categorize each finding:
- scan: sequential scans, bitmap scans, or full table reads
- join: nested loops, hash joins, or poor join strategies
- index: missing indexes, unused indexes, or covering index opportunities
- planner: row estimate mismatches, stale statistics, or poor cardinality estimates

Return ONLY a JSON object. No explanation, no preamble, no markdown code fences. Raw JSON only, exactly matching this schema:

{
  "summary": "2-3 sentence plain English summary of the overall problem",
  "total_time_ms": <number>,
  "overall_severity": "<critical|warning|suggestion>",
  "findings": [
    {
      "table": "<table name>",
      "finding_type": "<scan|join|index|planner>",
      "rows_scanned": <number>,
      "rows_expected": <number>,
      "rows_actual": <number>,
      "why": "Plain English explanation of why this is a problem",
      "recommendation": "Specific, actionable recommendation",
      "severity": "<critical|warning|suggestion>"
    }
  ]
}

The field for execution time must be named exactly total_time_ms.

Each finding must include a specific recommendation, not generic advice. The why field should be understandable to an engineer who is not a PostgreSQL expert."""

def validate_explain_output(explain_output: str) -> bool:
  if not explain_output or len(explain_output.strip()) < 50:
    return False
  
  has_timing = (
    "Planning Time" in explain_output and
    "Execution Time" in explain_output
  )

  has_plan_markers = any([
    "cost=" in explain_output,
    "rows=" in explain_output,
    "actual time=" in explain_output
  ])

  return has_timing and has_plan_markers


def analyze_explain_output(explain_output: str) -> AnalyzeResponse:
  if not validate_explain_output(explain_output):
    raise ValueError("Input does not appear to be a valid PostgreSQL EXPLAIN ANALYZE output.")
  response = client.messages.create(
    model="claude-opus-4-5",
    max_tokens=2000,
    temperature=0,
    messages=[
      {
        "role": "user",
        "content": explain_output
      }
    ],
    system=SYSTEM_PROMPT
  )

  raw = response.content[0].text
  data = json.loads(raw)

  # Normalize field names — LLM may return total_time instead of total_time_ms
  if "total_time" in data and "total_time_ms" not in data:
    data["total_time_ms"] = data.pop("total_time")

  return AnalyzeResponse(**data)