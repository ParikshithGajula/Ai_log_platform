import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
from bson import ObjectId

async def seed_sample_data():
    """Seed the database with sample log data from sample_errors.log"""
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.log_platform
    logs_collection = db.logs
    jobs_collection = db.jobs

    # Clear existing data
    await logs_collection.delete_many({})
    await jobs_collection.delete_many({})

    # Sample logs based on sample_errors.log
    base_time = datetime(2026, 3, 1, 10, 0, 0)

    sample_logs = [
        {
            "timestamp": base_time + timedelta(seconds=0),
            "level": "INFO",
            "service": "Auth-Service",
            "message": "Starting service on port 5000",
            "host": "prod-server-1",
            "trace_id": "trace-001",
            "anomaly_score": 0.0,
            "raw_line": "[2026-03-01T10:00:00Z] [INFO] Auth-Service: Starting service on port 5000"
        },
        {
            "timestamp": base_time + timedelta(seconds=5),
            "level": "INFO",
            "service": "Payment-Service",
            "message": "Starting service on port 5001",
            "host": "prod-server-2",
            "trace_id": "trace-002",
            "anomaly_score": 0.0,
            "raw_line": "[2026-03-01T10:00:05Z] [INFO] Payment-Service: Starting service on port 5001"
        },
        {
            "timestamp": base_time + timedelta(seconds=312),
            "level": "ERROR",
            "service": "Auth-Service",
            "message": "Connection to Redis failed! Error: timeout",
            "host": "prod-server-1",
            "trace_id": "trace-003",
            "anomaly_score": 0.85,
            "raw_line": "[2026-03-01T10:05:12Z] [ERROR] Auth-Service: Connection to Redis failed! Error: timeout"
        },
        {
            "timestamp": base_time + timedelta(seconds=315),
            "level": "WARN",
            "service": "Auth-Service",
            "message": "Retrying Redis connection 1/3",
            "host": "prod-server-1",
            "trace_id": "trace-004",
            "anomaly_score": 0.45,
            "raw_line": "[2026-03-01T10:05:15Z] [WARN] Auth-Service: Retrying Redis connection 1/3"
        },
        {
            "timestamp": base_time + timedelta(seconds=320),
            "level": "ERROR",
            "service": "Auth-Service",
            "message": "Connection to Redis failed! Error: timeout",
            "host": "prod-server-1",
            "trace_id": "trace-005",
            "anomaly_score": 0.85,
            "raw_line": "[2026-03-01T10:05:20Z] [ERROR] Auth-Service: Connection to Redis failed! Error: timeout"
        },
        {
            "timestamp": base_time + timedelta(seconds=322),
            "level": "CRITICAL",
            "service": "Auth-Service",
            "message": "Service shutting down due to Redis failure",
            "host": "prod-server-1",
            "trace_id": "trace-006",
            "anomaly_score": 0.95,
            "raw_line": "[2026-03-01T10:05:22Z] [CRITICAL] Auth-Service: Service shutting down due to Redis failure"
        },
        {
            "timestamp": base_time + timedelta(seconds=360),
            "level": "ERROR",
            "service": "Payment-Service",
            "message": "Auth-Service unreachable, returning 503 for all requests",
            "host": "prod-server-2",
            "trace_id": "trace-007",
            "anomaly_score": 0.88,
            "raw_line": "[2026-03-01T10:06:00Z] [ERROR] Payment-Service: Auth-Service unreachable, returning 503 for all requests"
        },
        {
            "timestamp": base_time + timedelta(seconds=365),
            "level": "WARN",
            "service": "Router",
            "message": "Dropping 245 incoming requests to Payment-Service",
            "host": "load-balancer-1",
            "trace_id": "trace-008",
            "anomaly_score": 0.72,
            "raw_line": "[2026-03-01T10:06:05Z] [WARN] Router: Dropping 245 incoming requests to Payment-Service"
        },
        {
            "timestamp": base_time + timedelta(seconds=600),
            "level": "ERROR",
            "service": "Database",
            "message": "Too many connections opened from unknown IP",
            "host": "db-server-1",
            "trace_id": "trace-009",
            "anomaly_score": 0.78,
            "raw_line": "[2026-03-01T10:10:00Z] [ERROR] Database: Too many connections opened from unknown IP"
        },
        {
            "timestamp": base_time + timedelta(seconds=720),
            "level": "FATAL",
            "service": "System",
            "message": "OOMKiller triggered. Out of memory. Killed process Payment-Service.",
            "host": "prod-server-2",
            "trace_id": "trace-010",
            "anomaly_score": 0.99,
            "raw_line": "[2026-03-01T10:12:00Z] [FATAL] System: OOMKiller triggered. Out of memory. Killed process Payment-Service."
        }
    ]

    # Insert logs
    result = await logs_collection.insert_many(sample_logs)
    print(f"Inserted {len(result.inserted_ids)} logs")

    # Create a sample job
    job_data = {
        "job_id": "JOB-20260301100512",
        "filename": "sample_errors.log",
        "status": "completed",
        "created_at": datetime.now(),
        "processed_count": 10,
        "anomalies": [
            {"log_id": str(result.inserted_ids[2]), "score": 0.85, "message": "Redis connection failure"},
            {"log_id": str(result.inserted_ids[4]), "score": 0.85, "message": "Redis connection failure"},
            {"log_id": str(result.inserted_ids[5]), "score": 0.95, "message": "Critical service shutdown"},
            {"log_id": str(result.inserted_ids[6]), "score": 0.88, "message": "Service unreachable"},
            {"log_id": str(result.inserted_ids[9]), "score": 0.99, "message": "System crash - OOM killer"}
        ]
    }

    await jobs_collection.insert_one(job_data)
    print(f"Created sample job: {job_data['job_id']}")

    client.close()
    print("Database seeding complete!")

if __name__ == "__main__":
    asyncio.run(seed_sample_data())
