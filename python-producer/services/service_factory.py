"""
Service factory following Dependency Inversion Principle
"""
from services.url_service import URLService
from services.html_service import HTMLService
from services.kafka_service import KafkaService
from services.cassandra_service import CassandraService
from services.redis_service import RedisService
from services.bloom_filter_service import BloomFilterService
from services.url_processor_service import URLProcessorService
from services.metrics_service import MetricsService


class ServiceFactory:
    """Factory for creating and managing service instances"""
    
    def __init__(self):
        self._services = {}
    
    def get_url_service(self) -> URLService:
        """Get URL service instance"""
        if 'url_service' not in self._services:
            self._services['url_service'] = URLService()
        return self._services['url_service']
    
    def get_html_service(self) -> HTMLService:
        """Get HTML service instance"""
        if 'html_service' not in self._services:
            self._services['html_service'] = HTMLService()
        return self._services['html_service']
    
    def get_kafka_service(self) -> KafkaService:
        """Get Kafka service instance"""
        if 'kafka_service' not in self._services:
            self._services['kafka_service'] = KafkaService()
        return self._services['kafka_service']
    
    def get_cassandra_service(self) -> CassandraService:
        """Get Cassandra service instance"""
        if 'cassandra_service' not in self._services:
            self._services['cassandra_service'] = CassandraService()
        return self._services['cassandra_service']
    
    def get_redis_service(self) -> RedisService:
        """Get Redis service instance"""
        if 'redis_service' not in self._services:
            self._services['redis_service'] = RedisService()
        return self._services['redis_service']
    
    def get_bloom_filter_service(self) -> BloomFilterService:
        """Get Bloom filter service instance"""
        if 'bloom_filter_service' not in self._services:
            self._services['bloom_filter_service'] = BloomFilterService()
        return self._services['bloom_filter_service']
    
    def get_metrics_service(self) -> MetricsService:
        """Get metrics service instance"""
        if 'metrics_service' not in self._services:
            self._services['metrics_service'] = MetricsService()
        return self._services['metrics_service']
    
    def get_url_processor_service(self) -> URLProcessorService:
        """Get URL processor service with all dependencies"""
        if 'url_processor_service' not in self._services:
            self._services['url_processor_service'] = URLProcessorService(
                self.get_url_service(),
                self.get_html_service(),
                self.get_cassandra_service(),
                self.get_bloom_filter_service(),
                self.get_kafka_service()
            )
        return self._services['url_processor_service']
    
    def initialize_all_services(self) -> None:
        """Initialize all services"""
        self.get_kafka_service().initialize_producer()
        self.get_kafka_service().initialize_consumer(
            'crawled-content',  # This should come from config
            'url-producer-group'  # This should come from config
        )
        self.get_cassandra_service().initialize()
        self.get_redis_service().initialize()
        self.get_bloom_filter_service().initialize()
        self.get_metrics_service().start_metrics_server()
    
    def cleanup_all_services(self) -> None:
        """Cleanup all services"""
        self.get_kafka_service().close()
        self.get_cassandra_service().close()
        self.get_redis_service().close()
