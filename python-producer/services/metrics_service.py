"""
Metrics service following Single Responsibility Principle
"""
from prometheus_client import Counter, Histogram, start_http_server
from loguru import logger

from config import Config


class MetricsService:
    """Service responsible for metrics collection and exposure"""
    
    def __init__(self):
        self._metrics_started = False
    
    def start_metrics_server(self) -> None:
        """Start Prometheus metrics server"""
        try:
            if not self._metrics_started:
                start_http_server(Config.METRICS_PORT)
                self._metrics_started = True
                logger.info(f"Metrics server started on port {Config.METRICS_PORT}")
        except Exception as e:
            logger.error(f"Failed to start metrics server: {e}")
            raise
    
    def get_urls_processed_counter(self) -> Counter:
        """Get URLs processed counter"""
        return Counter('urls_processed_total', 'Total URLs processed')
    
    def get_urls_discovered_counter(self) -> Counter:
        """Get URLs discovered counter"""
        return Counter('urls_discovered_total', 'Total new URLs discovered')
    
    def get_parsing_duration_histogram(self) -> Histogram:
        """Get parsing duration histogram"""
        return Histogram('parsing_duration_seconds', 'Time spent parsing HTML')
    
    def get_kafka_messages_sent_counter(self) -> Counter:
        """Get Kafka messages sent counter"""
        return Counter('kafka_messages_sent_total', 'Total Kafka messages sent')
    
    def get_kafka_messages_received_counter(self) -> Counter:
        """Get Kafka messages received counter"""
        return Counter('kafka_messages_received_total', 'Total Kafka messages received')
    
    def get_cassandra_operations_counter(self) -> Counter:
        """Get Cassandra operations counter"""
        return Counter('cassandra_operations_total', 'Total Cassandra operations', ['operation'])
    
    def get_redis_operations_counter(self) -> Counter:
        """Get Redis operations counter"""
        return Counter('redis_operations_total', 'Total Redis operations', ['operation'])
    
    def get_error_counter(self) -> Counter:
        """Get error counter"""
        return Counter('errors_total', 'Total errors', ['service', 'error_type'])
    
    def get_processing_time_histogram(self) -> Histogram:
        """Get processing time histogram"""
        return Histogram('processing_time_seconds', 'Time spent processing', ['service'])
