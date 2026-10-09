from fastapi import FastAPI, UploadFile, File, Path, Query, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
import os
import uuid
import json
import asyncio
import logging
from dotenv import load_dotenv
from datetime import datetime, timedelta
from bson import ObjectId
from bson.errors import InvalidId
from typing import List, Optional
from ai_analysis import AIAnalyzer
from database import db, init_db

load_dotenv()
logger = logging.getLogger("ai_log_platform")

# Lazy AI analyzer — never crashes import when OPENAI_API_KEY is missing
ai_analyzer = AIAnalyzer()

def serialize_doc(doc: dict) -> dict:
    """Convert MongoDB document to JSON-serializable dict (recursive)."""
    out = {}
    for k, v in doc.items():
        if isinstance(v, ObjectId):
            out[k] = str(v)
        elif isinstance(v, datetime):
            out[k] = v.isoformat()
        elif isinstance(v, dict):
            out[k] = serialize_doc(v)
        elif isinstance(v, list):
            out[k] = [serialize_doc(i) if isinstance(i, dict) else str(i) if isinstance(i, ObjectId) else i.isoformat() if isinstance(i, datetime) else i for i in v]
        else:
            out[k] = v
    return out

def _cors_origins() -> list:
    defaults = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://parikshithgajula.github.io",
        "https://shanmukha-3283.github.io",
    ]
    extra = os.getenv("CORS_EXTRA_ORIGINS", "")
    if extra:
        defaults.extend([o.strip() for o in extra.split(",") if o.strip()])
    # Deduplicate while preserving order
    seen, out = set(), []
    for o in defaults:
        if o not in seen:
            seen.add(o)
            out.append(o)
    return out

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(title="AI Log Platform", lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _logs_collection():
    return db.db["logs"]

def _jobs_collection():
    return db.db["jobs"]

@app.get("/health")
async def health_check():
    """Check if services are running"""
    try:
        # Test MongoDB connection via the shared client
        await db.client.admin.command("ping")
        mongo_ok = True
    except Exception as e:
        logger.warning("Health check mongo error: %s", e)
        mongo_ok = False
    
    try:
        # Test Redis connection — read from env, not hardcoded localhost
        import redis as redis_lib
        _redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        redis_client = redis_lib.from_url(_redis_url, socket_connect_timeout=2)
        redis_client.ping()
        redis_ok = True
    except Exception:
        redis_ok = False
    
    return {
        "status": "ok",
        "mongodb": mongo_ok,
        "redis": redis_ok
    }

MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))

@app.post("/upload-log")
async def upload_log(file: UploadFile = File(...)):
    """Queue a log file for background Celery processing."""
    filename = file.filename or "upload.log"
    if not filename.endswith((".log", ".txt")):
        raise HTTPException(status_code=400, detail="File must be .log or .txt")

    # Read first (UploadFile has no reliable .size); enforce limit on bytes
    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"File size exceeds {MAX_UPLOAD_BYTES // (1024*1024)}MB")

    # Unique job id (uuid suffix avoids same-second collisions)
    job_id = f"JOB-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"
    job_data = {
        "job_id": job_id,
        "filename": filename,
        "status": "queued",
        "created_at": datetime.now(),
    }

    # Store job in MongoDB (Motor async — must await)
    await _jobs_collection().insert_one(job_data)

    # NOTE: Celery .delay() is synchronous — do NOT await it
    from celery_worker import process_log_file
    process_log_file.delay(job_id, content.decode("utf-8", errors="replace"), filename)

    return {
        "job_id": job_id,
        "filename": filename,
        "status": "queued",
        "created_at": job_data["created_at"].isoformat()
    }

@app.get("/jobs/{job_id}")
async def get_job_status(job_id: str = Path(...)):
    """Poll async processing status and processed count."""
    job = await _jobs_collection().find_one({"job_id": job_id})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    created = job.get("created_at")
    return {
        "job_id": job["job_id"],
        "filename": job.get("filename", ""),
        "status": job.get("status", "unknown"),
        "created_at": created.isoformat() if isinstance(created, datetime) else str(created),
        "processed_count": job.get("processed_count", 0),
        "anomalies": job.get("anomalies", []),
        "error": job.get("error")
    }

@app.get("/logs")
async def get_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    service: Optional[str] = None,
    level: Optional[str] = None,
    min_anomaly_score: Optional[float] = None,
    anomaly_threshold: Optional[float] = None,  # backwards-compat alias for old frontend
    search: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None
):
    """Query logs with filters and pagination"""
    filter_query = {}

    # Add service filter
    if service:
        filter_query["service"] = service

    # Add level filter
    if level:
        filter_query["level"] = level

    # Add anomaly score filter (support legacy alias)
    threshold = min_anomaly_score if min_anomaly_score is not None else anomaly_threshold
    if threshold is not None:
        filter_query["anomaly_score"] = {"$gte": threshold}

    # Add search filter
    if search:
        filter_query["$text"] = {"$search": search}

    # Add time range filter (merge $gte/$lte — never overwrite)
    time_filter = {}
    if start_time:
        try:
            time_filter["$gte"] = datetime.fromisoformat(start_time)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_time; use ISO format")
    if end_time:
        try:
            time_filter["$lte"] = datetime.fromisoformat(end_time)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_time; use ISO format")
    if time_filter:
        filter_query["timestamp"] = time_filter

    # Pagination
    skip = (page - 1) * page_size
    limit = page_size

    # Get total count
    total = await _logs_collection().count_documents(filter_query)

    # Get paginated results
    cursor = _logs_collection().find(filter_query).skip(skip).limit(limit).sort("timestamp", -1)
    results = await cursor.to_list(length=limit)

    return {
        "logs": [serialize_doc(doc) for doc in results],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size
    }

@app.get("/analytics")
async def get_analytics():
    """Generate analytics about log data"""
    now = datetime.now()
    day_ago = now - timedelta(days=1)
    half_day_ago = now - timedelta(hours=12)
    # Total logs (last 24 hours)
    total_logs = await _logs_collection().count_documents({
        "timestamp": {"$gte": day_ago}
    })

    # Error count (level: ERROR)
    error_count = await _logs_collection().count_documents({
        "level": "ERROR",
        "timestamp": {"$gte": day_ago}
    })

    # Error rate
    error_rate = round(error_count / total_logs * 100, 2) if total_logs > 0 else 0

    # Top 5 services by log count
    top_services_cursor = _logs_collection().aggregate([
        {"$match": {"timestamp": {"$gte": day_ago}}},
        {"$group": {"_id": "$service", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 5}
    ])
    top_services = await top_services_cursor.to_list(length=5)

    # Anomalies (score >= 0.7)
    anomaly_count = await _logs_collection().count_documents({
        "anomaly_score": {"$gte": 0.7},
        "timestamp": {"$gte": day_ago}
    })

    # Hourly breakdown (last 12 hours) with totals + errors per bucket.
    # Bucket id is "%Y-%m-%d %H" so days never mix; hour label stays "%H".
    hourly_cursor = _logs_collection().aggregate([
        {"$match": {"timestamp": {"$gte": half_day_ago}}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d %H", "date": "$timestamp"}},
            "count": {"$sum": 1},
            "errors": {"$sum": {"$cond": [{"$eq": ["$level", "ERROR"]}, 1, 0]}},
        }},
        {"$sort": {"_id": 1}},
        {"$limit": 12},
    ])
    hourly_raw = await hourly_cursor.to_list(length=12)
    hourly_breakdown = [
        {
            "hour": b["_id"].split(" ")[1] if " " in str(b["_id"]) else str(b["_id"]),
            "bucket": b["_id"],
            "count": b["count"],
            # Aliases for frontend chart compatibility
            "total_logs": b["count"],
            "error_count": b.get("errors", 0),
        }
        for b in hourly_raw
    ]

    return {
        "total_logs": total_logs,
        "error_count": error_count,
        "error_rate": error_rate,
        "top_services": [{"service": service["_id"], "count": service["count"]} for service in top_services],
        "anomaly_count": anomaly_count,
        "hourly_breakdown": hourly_breakdown,
        # Backwards-compat alias for older frontend (hourly_data)
        "hourly_data": hourly_breakdown,
    }

@app.post("/analyze")
async def analyze_logs():
    """AI analysis of log data"""
    # This would typically involve more complex analysis
    return {
        "message": "AI analysis endpoint",
        "suggestion": "Consider implementing machine learning models for pattern detection"
    }


class AskAIRequest(BaseModel):
    query: str
    log_ids: List[str] = []
    model: str = "gpt-4o"


@app.post("/ask-ai")
async def ask_ai(request: AskAIRequest):
    """AI-powered log analysis with SSE streaming response"""
    query = request.query
    log_ids = request.log_ids
    model_choice = request.model

    # Validate ObjectIds before streaming (raising here returns proper 400)
    object_ids = []
    if log_ids:
        try:
            object_ids = [ObjectId(lid) for lid in log_ids]
        except (InvalidId, TypeError):
            raise HTTPException(status_code=400, detail="Invalid log_ids; must be Mongo ObjectIds")

    async def event_stream():
        try:
            # Fetch relevant logs for context
            filter_query = {"_id": {"$in": object_ids}} if object_ids else {}

            cursor = _logs_collection().find(filter_query).sort("timestamp", -1).limit(50)
            recent_logs = await cursor.to_list(length=50)

            # Build initial context
            services = list(set(l.get("service", "unknown") for l in recent_logs))

            # Initial summary for streaming
            response_text = f"Neural Link established. Routing inquiry to {model_choice}...\n"
            response_text += f"Analyzing {len(recent_logs)} transmission logs across {len(services)} services.\n"
            
            words = response_text.split(" ")
            for word in words:
                yield f"data: {json.dumps({'token': word + ' '})}\n\n"
                await asyncio.sleep(0.04)

            # --- REAL AI ANALYSIS ---
            try:
                log_texts = [f"[{l.get('level')}] {l.get('service')}: {l.get('message')}" for l in recent_logs[:15]]
                analysis = await ai_analyzer.analyze_root_cause(log_texts, model=model_choice)
                
                result = {
                    "cause": analysis.get("cause", "Analysis inconclusive"),
                    "confidence": analysis.get("confidence", "MEDIUM"),
                    "severity": analysis.get("severity", "MEDIUM"),
                    "affected_services": analysis.get("affected_services", services[:3]),
                    "recommendation": analysis.get("recommendation", "Review system health monitors."),
                    "impact": analysis.get("impact", "Service degradation likely."),
                    "solution": analysis.get("solution", "Manual inspection required.")
                }
            except Exception as ai_err:
                logger.warning("AI error: %s", ai_err)
                result = {
                    "cause": "AI subsystem busy or unavailable.",
                    "confidence": "LOW",
                    "severity": "HIGH",
                    "affected_services": services[:3],
                    "impact": "Service degradation likely.",
                    "recommendation": "Try a different model or check API quota.",
                    "solution": "Check backend .env for valid OPENAI_API_KEY."
                }

            yield f"data: {json.dumps({'done': True, 'result': result})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'done': True, 'result': {'error': str(e)}})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/stream")
async def stream_logs():
    """Stream latest logs snapshot (10 docs) as SSE."""
    async def event_stream():
        cursor = _logs_collection().find().sort("timestamp", -1).limit(10)
        docs = await cursor.to_list(length=10)
        for doc in docs:
            yield f"data: {json.dumps(serialize_doc(doc))}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
