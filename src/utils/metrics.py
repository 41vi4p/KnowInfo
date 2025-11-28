"""
Prometheus metrics for monitoring
"""
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import time
from functools import wraps

# Counters
content_ingested_total = Counter(
    'content_ingested_total',
    'Total content items ingested',
    ['source', 'status']
)

claims_extracted_total = Counter(
    'claims_extracted_total',
    'Total claims extracted',
    ['category', 'priority']
)

verifications_completed_total = Counter(
    'verifications_completed_total',
    'Total verifications completed',
    ['status', 'confidence_level']
)

whatsapp_queries_total = Counter(
    'whatsapp_queries_total',
    'Total WhatsApp queries received'
)

# Histograms
verification_duration_seconds = Histogram(
    'verification_duration_seconds',
    'Time taken to verify a claim'
)

whatsapp_response_duration_seconds = Histogram(
    'whatsapp_response_duration_seconds',
    'Time taken to respond to WhatsApp query'
)

claim_extraction_duration_seconds = Histogram(
    'claim_extraction_duration_seconds',
    'Time taken to extract claims from content'
)

# Gauges
active_monitors = Gauge(
    'active_monitors',
    'Number of active content monitors'
)

pending_verifications = Gauge(
    'pending_verifications',
    'Number of claims pending verification'
)

trending_claims_current = Gauge(
    'trending_claims_current',
    'Current number of trending claims'
)


def track_time(metric: Histogram):
    """Decorator to track execution time"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start
                metric.observe(duration)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start
                metric.observe(duration)

        # Return appropriate wrapper
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def get_metrics():
    """Get current metrics in Prometheus format"""
    return generate_latest()
