import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from app.models import AnalyzeRequest, AnalyzeResponse
from app.analyzer import analyze_explain_output

load_dotenv()

app = FastAPI(
  title="EXPLAIN Analyzer",
  description="Submit a PostgreSQL EXPLAIN ANALYZE output and get a structured performance analysis.",
  version="0.1.0"
)

@app.get("/", include_in_schema=False)
def root():
  return RedirectResponse(url="/docs")

@app.get("/health")
def health_check():
  api_key = os.getenv("ANTHROPIC_API_KEY")
  if not api_key:
    raise HTTPException(status_code=503, detail="Anthropic API key not configured.")
  return {"status": "ok"}

@app.post("/v1/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest):
  try:
    result = analyze_explain_output(request.explain_output)
    return result
  except ValueError as e:
    raise HTTPException(status_code=422, detail=str(e))
  except Exception as e:
    raise HTTPException(status_code=500, detail="Analysis failed. Please check your EXPLAIN ANALYZE output and try again.")