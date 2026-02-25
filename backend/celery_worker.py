import os
import json
from celery import Celery
from pymongo import MongoClient
from backend.parser import LogParser
from backend.anomaly import AnomalyDetector
try:
    from backend.ai_analysis import AIAnalyzer
except Exception:
    AIAnalyzer = None

# Initialize Celery
celery_app = Celery(
    "worker",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
)

# Initialize MongoDB
client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017/"))
db = client["log_platform"]

@celery_app.task(name="process_log_file")
def process_log_file(job_id, content, filename):
    """Process log file and store results in MongoDB"""
    try:
        # 1. Parse logs
        parser = LogParser()
        parsed_logs = parser.parse(content)
        
        # 2. Detect anomalies
        detector = AnomalyDetector()
        anomaly_results = detector.detect(parsed_logs)
        
        # 3. Generate embeddings (if needed)
        # analyzer = AIAnalyzer()
        # embeddings = analyzer.generate_embeddings(anomaly_results)
        
        # 4. Store results in MongoDB
        db.jobs.update_one(
            {"job_id": job_id},
            {
                "$set": {
                    "status": "completed",
                    "processed_count": len(anomaly_results),
                    "anomalies": anomaly_results,
                    "filename": filename
                }
            }
        )
    except Exception as e:
        db.jobs.update_one(
            {"job_id": job_id},
            {
                "$set": {
                    "status": "failed",
                    "error": str(e)
                }
            }
        )
