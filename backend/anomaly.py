import statistics
from collections import defaultdict
from typing import List, Dict, Any
from datetime import datetime

class AnomalyDetector:
    # Constants for anomaly detection tuning
    MIN_STD_OFFSET = 0.001  # Avoid division by zero
    ANOMALY_Z_THRESHOLD = 2  # Z-score threshold: 2σ deviation marks anomaly

    def compute_anomaly_score(self, logs: List[Dict]) -> List[Dict]:
        """
        Compute anomaly scores for logs based on hourly error rate deviations.
        
        Scores are computed per service: each hour's error rate is compared to
        the service's historical mean and standard deviation. A high deviation
        (> 2σ) indicates an anomaly.
        
        Args:
            logs: List of log dicts with required keys: 'service', 'timestamp', 'level'.
                  timestamp must be a datetime object.
                  level is expected to be normalized to uppercase (e.g., 'ERROR', 'WARN', 'INFO')
                  by the parser.
        
        Returns:
            Same list with added 'anomaly_score' key (0.0 = normal, 1.0 = anomaly).
            Modifies logs in-place.
        
        Raises:
            KeyError: If any log is missing 'service', 'timestamp', or 'level'.
            TypeError: If timestamp is not a datetime object.
        """
        # Input validation
        if not logs:
            return []
        
        required_keys = {'service', 'timestamp', 'level'}
        for log in logs:
            if not required_keys.issubset(log.keys()):
                raise KeyError(f"Log missing required field(s): {required_keys - log.keys()}")
            if not isinstance(log['timestamp'], datetime):
                raise TypeError(f"Expected datetime for 'timestamp', got {type(log['timestamp'])}")
        # Group logs by service name
        services = defaultdict(list)
        for log in logs:
            service = log['service']
            services[service].append(log)
        
        # Process each service
        for service, service_logs in services.items():
            # Group logs into (date, hour) buckets — hour-only mixes days
            hourly_buckets = defaultdict(list)
            for log in service_logs:
                ts = log['timestamp']
                # Accept ISO strings defensively (e.g. from Mongo round-trip)
                if isinstance(ts, str):
                    try:
                        ts = datetime.fromisoformat(ts)
                        log['timestamp'] = ts
                    except Exception:
                        continue
                bucket = (ts.date().isoformat(), ts.hour)
                hourly_buckets[bucket].append(log)
            
            # Compute error rates for each bucket
            # Note: assumes parser normalizes levels to uppercase (e.g., 'ERROR', 'WARN', 'INFO')
            hour_to_error_rate = {}
            for hour, logs_in_bucket in hourly_buckets.items():
                errors_count = sum(1 for log in logs_in_bucket if log['level'] == 'ERROR')
                total_logs = len(logs_in_bucket)
                error_rate = errors_count / total_logs if total_logs > 0 else 0.0
                hour_to_error_rate[hour] = error_rate
            
            # Collect all error rates for the service
            error_rates = list(hour_to_error_rate.values())
            
            # Compute mean and standard deviation over (date, hour) buckets.
            if not error_rates:
                # No logs with this service in this batch — skip
                continue
            
            if len(error_rates) < 2:
                # Single-bucket batch (e.g. all logs share one hour):
                # fall back to global error rate so spikes still score.
                # A bucket that is 100% errors with a healthy global rate => anomaly.
                global_errors = sum(1 for l in service_logs if l['level'] == 'ERROR')
                global_rate = global_errors / len(service_logs) if service_logs else 0.0
                mean = global_rate * 0.5  # baseline below observed spike
                std = max(global_rate * 0.5, 0.1)
            else:
                try:
                    mean = statistics.mean(error_rates)
                    std = statistics.stdev(error_rates)
                except statistics.StatisticsError:
                    mean = statistics.mean(error_rates)
                    std = 0.0
            
            # Now, compute score for each log in service_logs
            for log in service_logs:
                ts = log['timestamp']
                bucket = (ts.date().isoformat(), ts.hour) if isinstance(ts, datetime) else None
                error_rate = hour_to_error_rate.get(bucket, 0.0)
                
                # Compute Z-score: how many standard deviations from the mean
                denominator = std + self.MIN_STD_OFFSET
                z_score = (error_rate - mean) / denominator
                
                # Check if this hour's error rate exceeds the anomaly threshold (2σ)
                if error_rate > mean + self.ANOMALY_Z_THRESHOLD * std:
                    score = 1.0
                else:
                    # Use Z-score normalized to [0, 1)
                    score = z_score
                    score = max(0.0, min(1.0, score))
                
                log['anomaly_score'] = score
        
        return logs
