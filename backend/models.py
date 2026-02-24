from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class LogDocument(BaseModel):
    id: Optional[str] = Field(None, description="Unique identifier for the log entry")
    timestamp: datetime = Field(..., description="When the log was created")
    level: str = Field(..., description="Log severity: INFO/WARN/ERROR/DEBUG/UNKNOWN")
    service: str = Field(..., description="Which service generated the log")
    message: str = Field(..., description="The log message content")
    host: str = Field(..., description="Hostname of the machine where the log originated")
    trace_id: Optional[str] = Field(None, description="Correlation ID for distributed systems")
    anomaly_score: float = Field(0.0, description="AI-assigned score for potential anomalies")
    raw_line: str = Field(..., description="Original log line from the source")

class UploadResponse(BaseModel):
    job_id: str = Field(..., description="Unique identifier for the upload job")
    filename: str = Field(..., description="Name of the uploaded file")
    status: str = Field(..., description="Upload status: success/failure")
    message: str = Field(..., description="Additional information about the upload")

class JobStatus(BaseModel):
    job_id: str = Field(..., description="Unique identifier for the job")
    status: str = Field(..., description="Job status: queued/processing/completed/failed")
    processed_count: Optional[int] = Field(None, description="Number of logs processed")
    error: Optional[str] = Field(None, description="Error message if job failed")

class AnalyticsResponse(BaseModel):
    total_logs: int = Field(..., description="Total number of logs in the system")
    error_count: int = Field(..., description="Number of ERROR level logs")
    warn_count: int = Field(..., description="Number of WARN level logs")
    error_rate: float = Field(..., description="Percentage of ERROR logs")
    top_services: List[str] = Field(..., description="Top services by log volume")
    anomaly_count: int = Field(..., description="Number of flagged anomalies")
    hourly_breakdown: List[dict] = Field(..., description="Logs grouped by hour")

class AskAIRequest(BaseModel):
    query: str = Field(..., description="User's question about the logs")
    log_ids: Optional[List[str]] = Field(None, description="Specific logs to analyze")