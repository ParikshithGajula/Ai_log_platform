"""Unit tests: parser timestamps/levels + anomaly date-hour grouping. No DB required."""
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from parser import LogParser
from anomaly import AnomalyDetector


def test_app_log_pattern():
    p = LogParser()
    r = p.parse_line("2024-12-01 03:17:44 ERROR payment-svc - DB conn failed")
    assert r["level"] == "ERROR"
    assert r["service"] == "payment-svc"
    assert r["timestamp"] == datetime(2024, 12, 1, 3, 17, 44)


def test_syslog_keeps_timestamp_and_level():
    p = LogParser()
    r = p.parse_line("Dec  1 03:17:44 prod-server-01 nginx[1234]: DB connection timeout after 30000ms")
    assert r["host"] == "prod-server-01"
    assert r["service"] == "nginx"
    assert r["level"] == "ERROR"  # inferred from message
    assert (r["timestamp"].month, r["timestamp"].day) == (12, 1)
    assert (r["timestamp"].hour, r["timestamp"].minute) == (3, 17)


def test_apache_keeps_timestamp_and_status_level():
    p = LogParser()
    r = p.parse_line('192.168.1.1 - - [01/Dec/2024:03:17:44 +0000] "GET /api HTTP/1.1" 500 1234')
    assert r["level"] == "ERROR"
    assert r["service"] == "web-server"
    assert r["timestamp"] == datetime(2024, 12, 1, 3, 17, 44)


def test_anomaly_groups_by_date_not_hour_only():
    det = AnomalyDetector()
    base = datetime(2024, 12, 1, 3, 0, 0)
    logs = []
    # Day 1, 3am: healthy (10 INFO)
    for i in range(10):
        logs.append({"service": "svc", "timestamp": base + timedelta(minutes=i), "level": "INFO"})
    # Day 2, 3am: spike (10 ERROR) — must score high despite same hour number
    for i in range(10):
        logs.append({"service": "svc", "timestamp": base + timedelta(days=1, minutes=i), "level": "ERROR"})
    scored = det.compute_anomaly_score(logs)
    spike_scores = [l["anomaly_score"] for l in scored[10:]]
    healthy_scores = [l["anomaly_score"] for l in scored[:10]]
    assert max(spike_scores) > max(healthy_scores), f"{spike_scores} vs {healthy_scores}"
    assert max(spike_scores) >= 0.7


def test_anomaly_single_bucket_spike_scores():
    det = AnomalyDetector()
    base = datetime.now().replace(microsecond=0)
    logs = [{"service": "s", "timestamp": base, "level": "INFO"} for _ in range(5)]
    logs += [{"service": "s", "timestamp": base, "level": "ERROR"} for _ in range(5)]
    scored = det.compute_anomaly_score(logs)
    # 50% error single bucket should not all be zero
    assert any(l["anomaly_score"] > 0 for l in scored)
