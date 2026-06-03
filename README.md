# EXPLAIN Analyzer

EXPLAIN Analyzer is a tool that takes a PostgreSQL EXPLAIN ANALYZE query plan and returns a structured performance analysis. It's built for developers who want to identify and understand query performance problems without being a PostgreSQL expert. It surfaces issues like missing indexes, sequential scans, and poor planner estimates alongside easy to understand explanations and actionable recommendations.

**Live API:** https://explain-analyzer.onrender.com/docs

## Motivation

I built this after spending too much time staring at query plan output, not fully sure how to interpret it or where to even start. Parsing EXPLAIN ANALYZE output is tedious and what to target is easy to miss if you don't already know what to look for. I wanted a tool that could do initial triage for me and explain the problems simply and clearly.

## Prerequisites

- Python 3.10+
- pip

## Running Locally

1. Clone the repo
2. Create a `.env` file with `ANTHROPIC_API_KEY=your_key_here`
3. Create a virtual environment: `python3 -m venv venv`
4. Activate your virtual environment: `source venv/bin/activate`
5. Install dependencies: `pip install -r requirements.txt`
6. Start the server: `uvicorn app.main:app --reload`

The API will be running at `http://127.0.0.1:8000`. Interactive documentation is available at `http://127.0.0.1:8000/docs`.

## Example

Request:

```bash
curl -X POST http://127.0.0.1:8000/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"explain_output": "your EXPLAIN ANALYZE output here"}'
```

Response:

```json
{
  "summary": "This query is performing a sequential scan on the enrollments table, scanning over 16 million rows to find 892K matching rows. Adding a composite index on school_id and state would dramatically reduce query time.",
  "total_time_ms": 4893.234,
  "overall_severity": "critical",
  "findings": [
    {
      "finding_type": "scan",
      "table": "enrollments",
      "rows_scanned": 16594668,
      "rows_expected": 2677023,
      "rows_actual": 892341,
      "why": "The enrollments table is being fully scanned in parallel, examining over 16 million total rows just to find 892K matching rows.",
      "recommendation": "CREATE INDEX CONCURRENTLY idx_enrollments_school_state ON enrollments(school_id, state)",
      "severity": "critical"
    }
  ]
}
```

## Design Decisions

**`temperature=0`**
The Anthropic API defaults to a temperature that allows some response variation. For a tool that needs to categorize findings consistently, that variation is undesirable. Setting `temperature=0` makes responses highly consistent in that the model always selects the highest probability output rather than sampling randomly.

**Pydantic validation on request and response**
The LLM sits at an unpredictable boundary where it can return unexpected field names, wrong types, or missing fields. Pydantic models enforce the data contract at that boundary in both directions. Invalid requests are rejected before they reach Claude. Invalid responses from Claude are caught before they reach the caller.

**Input validation before calling Claude**
Sending garbage input to Claude wastes an API call and returns a misleading 200 response. A lightweight check for EXPLAIN ANALYZE markers (Planning Time, Execution Time) rejects invalid input with a 422 before spending a token.

**Finding types**
Findings are categorized as `scan`, `join`, `index`, or `planner`. This gives callers a structured way to filter, prioritize, and display findings. A frontend could group by type, or a caller could filter to only `critical scan` findings.

**Severity classifications**
Three tiers defined by production impact rather than arbitrary labels. `critical` means the problem is causing measurable performance degradation or cost impact now. `warning` means noticeable impact that will worsen under load. `suggestion` means worth monitoring as the system scales.

**Defensive field normalization**
LLMs can return inconsistent field names even with explicit schema instructions. The parsing layer normalizes known variants before Pydantic validation runs rather than assuming the model is always consistent.

## API Reference

`POST /v1/analyze`

Analyzes a PostgreSQL EXPLAIN ANALYZE query plan and returns structured performance findings.

**Request body:**
```json
{
  "explain_output": "string"
}
```

**Response:**
```json
{
  "summary": "string",
  "total_time_ms": "float",
  "overall_severity": "critical | warning | suggestion",
  "findings": [
    {
      "finding_type": "scan | join | index | planner",
      "table": "string",
      "rows_scanned": "integer | null",
      "rows_expected": "integer | null",
      "rows_actual": "integer | null",
      "why": "string",
      "recommendation": "string",
      "severity": "critical | warning | suggestion"
    }
  ]
}
```

`GET /health`

Returns `{"status": "ok"}` if the service is running and configured correctly.