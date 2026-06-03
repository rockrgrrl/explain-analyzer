from pydantic import BaseModel
from typing import List, Optional
from enum import Enum


class Severity(str, Enum):
    critical = "critical"
    warning = "warning"
    suggestion = "suggestion"


class FindingType(str, Enum):
    scan = "scan"
    join = "join"
    index = "index"
    planner = "planner"


class Finding(BaseModel):
    finding_type: FindingType
    table: str
    rows_scanned: Optional[int] = None
    rows_expected: Optional[int] = None
    rows_actual: Optional[int] = None
    why: str
    recommendation: str
    severity: Severity


class AnalyzeRequest(BaseModel):
    explain_output: str


class AnalyzeResponse(BaseModel):
    summary: str
    total_time_ms: float
    overall_severity: Severity
    findings: List[Finding]