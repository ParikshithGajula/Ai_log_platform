# AI Log Platform

An end-to-end observability platform that ingests raw logs, parses and enriches them, detects anomalies, and provides AI-assisted root-cause analysis through a modern React dashboard.

## Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Core Features](#core-features)
- [Tech Stack](#tech-stack)
- [Repository Structure](#repository-structure)
- [How It Works](#how-it-works)
- [API Endpoints](#api-endpoints)
- [Quick Start (Docker - Recommended)](#quick-start-docker---recommended)
- [Local Development (Without Docker)](#local-development-without-docker)
- [Environment Variables](#environment-variables)
- [Running Tests](#running-tests)
- [Deployment Notes](#deployment-notes)
- [Troubleshooting](#troubleshooting)
- [Roadmap Ideas](#roadmap-ideas)

## Overview
AI Log Platform is designed to simulate a production-style log intelligence pipeline:

1. Upload `.log` / `.txt` files.
2. Process logs asynchronously via Celery workers.
3. Parse common log formats into normalized fields.
4. Score anomalies from time-windowed error rates.
5. Store structured logs in MongoDB with indexes.
6. Query logs/analytics from a FastAPI backend.
7. Ask AI for root-cause analysis with streaming responses (SSE).
8. Visualize everything in a React + Vite dashboard.

This makes the project useful both as a learning platform and as a practical starting point for a lightweight log observability system.

## Architecture

```text
[React Frontend]  -->  [FastAPI Backend]  -->  [MongoDB]
                           |       |
                           |       --> [OpenAI API] (for /ask-ai)
                           v
                        [Redis]
                           |
                        [Celery Worker]
```

### Data flow
- User uploads a file via the frontend.
- Backend creates a job record and queues processing in Celery.
- Worker parses lines, detects anomalies, and writes normalized logs to MongoDB.
- Frontend polls job status and fetches logs/analytics.
- `/ask-ai` streams AI-generated incident analysis back to the UI.

## Core Features

- **Asynchronous ingestion pipeline** with queue-backed processing.
- **Multiple log format support** (app logs, syslog-style, bracketed levels, Apache/Nginx-style).
- **Anomaly detection** based on error-rate spikes across service/time windows.
- **Search and filtering** by service, level, free-text, and score thresholds.
- **Analytics dashboard** (error rate, top services, hourly activity, anomaly count).
- **AI assistant for incidents** with structured root-cause output and confidence/severity fields.
- **Health checks** for MongoDB and Redis connectivity.

## Tech Stack

### Backend
- FastAPI + Uvicorn
- Celery + Redis
- MongoDB (Motor async client)
- OpenAI API integration
- NumPy / FAISS (vector-ready dependencies)

### Frontend
- React 19
- Vite
- Recharts
- Axios

### Infra / Packaging
- Docker + Docker Compose
- Render deployment config (`render.yaml`)

## Repository Structure

```text
Ai_log_platform/
├── backend/
│   ├── main.py              # FastAPI app + API endpoints
│   ├── celery_worker.py     # Background ingestion/processing pipeline
│   ├── parser.py            # Regex-based log parsing
│   ├── anomaly.py           # Statistical anomaly scoring
│   ├── ai_analysis.py       # OpenAI-powered root-cause analysis
│   ├── database.py          # MongoDB connection + index initialization
│   ├── models.py            # Pydantic data models
│   ├── e2e_test.py          # End-to-end integration script
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── api/client.js
│   │   └── components/*
│   ├── package.json
│   ├── vite.config.js
│   └── Dockerfile
├── docker-compose.yml
├── render.yaml
└── README.md
```

## How It Works

### 1) Upload + job creation
`POST /upload-log` validates file type/size, creates a `job_id`, stores initial job metadata in MongoDB, and enqueues a Celery task.

### 2) Parsing + enrichment in worker
Worker reads each line and maps it into structured fields:
- `timestamp`
- `level`
- `service`
- `message`
- `host`
- `raw_line`

### 3) Anomaly scoring
Detected over traffic windows and attached to each log as `anomaly_score`.

### 4) Query + analytics
Backend exposes paginated logs with filters and analytics summaries for charts/cards.

### 5) AI-assisted RCA
`POST /ask-ai` streams progress and returns JSON-style root-cause output:
- cause
- impact
- solution
- confidence
- severity
- affected services

## API Endpoints

### Health
- `GET /health`
  - Returns service status and MongoDB/Redis connectivity flags.

### Ingestion
- `POST /upload-log`
  - Multipart file upload (`.log` / `.txt`, max 10MB).
  - Returns `job_id`.
- `GET /jobs/{job_id}`
  - Poll async processing status and processed count.

### Logs
- `GET /logs`
  - Query params:
    - `page` (default `1`)
    - `page_size` (default `10`, max `100`)
    - `service`
    - `level`
    - `min_anomaly_score`
    - `search`
    - `start_time` / `end_time` (ISO format)

### Analytics
- `GET /analytics`
  - Returns totals, error count/rate, top services, hourly breakdown, anomaly count.

### AI
- `POST /ask-ai`
  - Body:
    ```json
    {
      "query": "Why is payment-svc failing?",
      "log_ids": [],
      "model": "gpt-4o"
    }
    ```
  - Response is **SSE** (`text/event-stream`) with tokens and final result payload.

## Quick Start (Docker - Recommended)

### Prerequisites
- Docker + Docker Compose
- OpenAI API key (optional but recommended for `/ask-ai`)

### 1) Configure backend env
Create `backend/.env.docker` (if not present):

```env
MONGO_URI=mongodb://mongodb:27017/
REDIS_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
OPENAI_API_KEY=your_openai_api_key
```

### 2) Build and run
```bash
docker compose up --build
```

### 3) Access services
- Frontend: `http://localhost:3000`
- Backend API docs: `http://localhost:8000/docs`
- Health endpoint: `http://localhost:8000/health`

## Local Development (Without Docker)

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Celery worker (separate terminal)
```bash
cd backend
source .venv/bin/activate
celery -A celery_worker worker --loglevel=info
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Frontend dev server usually runs on `http://localhost:5173`.

## Environment Variables

### Backend
- `MONGO_URI` - MongoDB connection string.
- `REDIS_URL` - Redis connection string (broker).
- `CELERY_RESULT_BACKEND` - Celery result backend.
- `OPENAI_API_KEY` - API key for AI analysis.

### Frontend
- `VITE_API_URL` - Backend base URL.

## Running Tests

### End-to-end integration check
This script generates test logs, uploads them, waits for processing, verifies analytics, and calls `/ask-ai`.

```bash
cd backend
python e2e_test.py
# or custom backend URL
BASE_URL=http://localhost:8000 python e2e_test.py
```

## Deployment Notes

- `render.yaml` includes service definitions for:
  - FastAPI web service
  - Celery worker
  - Redis
- Frontend is configured for static deployment (`frontend/vercel.json`) and supports GitHub Pages deployment scripts.

## Troubleshooting

- **Backend unreachable**: verify `docker compose ps` and `GET /health`.
- **Jobs stay queued**: ensure worker is running and Redis URL is correct.
- **No logs after "success"**: confirm `MONGO_URI` points to `mongodb` service (not localhost inside containerized worker).
- **AI result missing**: check `OPENAI_API_KEY` and request quota.
- **CORS/SSE issues**: verify frontend URL is allowed in backend CORS settings.

For known beginner issues and deeper fixes, see:
- `FINAL_ISSUES.md`
- `WHAT_YOU_BUILT.md`

## Roadmap Ideas

- JWT auth and role-based access.
- WebSocket live-tail stream.
- Persist and restore vector indexes on startup.
- Alerting integrations (Slack/email/PagerDuty).
- Multi-tenant project/workspace support.
- SLO/error-budget tracking and alert rules.

---

If this project helps you, consider extending it with one production feature at a time and documenting your architecture decisions as you scale.
