import os
import json
from celery import Celery
from pymongo import MongoClient
# Use direct imports (not 'backend.parser') because this file IS inside the backend dir
from parser import LogParser
from anomaly import AnomalyDetector
try:
    from ai_analysis import AIAnalyzer
except Exception:
    AIAnalyzer = None

# ─────────────────────────────────────────────────────────────
# Celery app — uses Redis as broker AND result backend
# ─────────────────────────────────────────────────────────────
celery_app = Celery(
    "worker",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND",
                      os.getenv("REDIS_URL", "redis://localhost:6379/0")),
)

# ─────────────────────────────────────────────────────────────
# MongoDB — MONGO_URI primary, MONGODB_URL/MONGODB_URI fallbacks
# (matches database.py + render.yaml + .env.example)
# ─────────────────────────────────────────────────────────────
def _mongo_uri() -> str:
    import os as _os
    return (
        _os.getenv("MONGO_URI")
        or _os.getenv("MONGODB_URL")
        or _os.getenv("MONGODB_URI")
        or "mongodb://localhost:27017/"
    )


client = MongoClient(_mongo_uri())
db = client["log_platform"]


@celery_app.task(name="process_log_file", bind=True, max_retries=2, time_limit=600)
def process_log_file(self, job_id: str, content: str, filename: str):
    """
    Background task: parse → detect anomalies → store results in MongoDB.
    This runs inside the Celery worker container, NOT in the web server.
    """
    try:
        # Mark processing so the frontend stops showing "queued" forever
        db.jobs.update_one({"job_id": job_id}, {"$set": {"status": "processing"}})

        # Guard: refuse absurd payloads through the broker (10MB cap)
        if content and len(content) > 10 * 1024 * 1024:
            raise ValueError("Log content exceeds 10MB worker limit")

        # ── 1. Parse log lines ──────────────────────────────────
        parser = LogParser()
        # content is a str (decoded by the API before handing to Celery)
        parsed_logs = parser.parse_file(content)

        # ── 2. Detect anomalies ───────────────────────────────
        # AnomalyDetector.compute_anomaly_score() adds 'anomaly_score' to each log
        detector = AnomalyDetector()
        try:
            scored_logs = detector.compute_anomaly_score(parsed_logs)
        except Exception as e:
            print(f"Anomaly scoring failed ({e}); storing parsed logs without scores")
            for log in parsed_logs:
                log.setdefault("anomaly_score", 0.0)
            scored_logs = parsed_logs

        # ── 3. Store each log entry in MongoDB (batched) ──────
        if scored_logs:
            for i in range(0, len(scored_logs), 1000):
                db.logs.insert_many(scored_logs[i:i + 1000], ordered=False)

        # ── 4. Mark job completed ─────────────────────────────
        db.jobs.update_one(
            {"job_id": job_id},
            {
                "$set": {
                    "status": "completed",
                    "processed_count": len(scored_logs),
                    "filename": filename,
                }
            },
        )

    except Exception as e:
        # Mark job failed so the API can report what went wrong
        db.jobs.update_one(
            {"job_id": job_id},
            {
                "$set": {
                    "status": "failed",
                    "error": str(e),
                }
            },
        )
        # Re-raise so Celery marks the task as FAILURE (visible in Flower)
        raise
