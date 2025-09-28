"""
Kafka service following Single Responsibility Principle
"""
import json
from typing import Optional, Dict, Any
from kafka import KafkaProducer, KafkaConsumer
from loguru import logger

from config import Config
from models import KafkaMessage


class KafkaService:
    """Service responsible for Kafka operations"""
    
    def __init__(self):
        self._producer: Optional[KafkaProducer] = None
        self._consumer: Optional[KafkaConsumer] = None
    
    def initialize_producer(self) -> None:
        """Initialize Kafka producer"""
        try:
            self._producer = KafkaProducer(
                bootstrap_servers=Config.get_kafka_servers(),
                value_serializer=lambda v: v.encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None
            )
            logger.info("Kafka producer initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {e}")
            raise
    
    def initialize_consumer(self, topic: str, group_id: str) -> None:
        """Initialize Kafka consumer"""
        try:
            self._consumer = KafkaConsumer(
                topic,
                bootstrap_servers=Config.get_kafka_servers(),
                value_deserializer=lambda m: m.decode('utf-8'),
                group_id=group_id
            )
            logger.info(f"Kafka consumer initialized for topic: {topic}")
        except Exception as e:
            logger.error(f"Failed to initialize Kafka consumer: {e}")
            raise
    
    def send_message(self, topic: str, key: str, value: str) -> None:
        """
        Send message to Kafka topic
        
        Args:
            topic: Kafka topic name
            key: Message key
            value: Message value
        """
        try:
            if not self._producer:
                raise RuntimeError("Kafka producer not initialized")
            
            self._producer.send(topic, key=key, value=value)
            self._producer.flush()
            logger.debug(f"Sent message to {topic}: {key}")
        except Exception as e:
            logger.error(f"Failed to send message to {topic}: {e}")
            raise
    
    def send_json_message(self, topic: str, key: str, data: Dict[str, Any]) -> None:
        """
        Send JSON message to Kafka topic
        
        Args:
            topic: Kafka topic name
            key: Message key
            data: Data to serialize as JSON
        """
        try:
            json_value = json.dumps(data)
            self.send_message(topic, key, json_value)
        except Exception as e:
            logger.error(f"Failed to send JSON message to {topic}: {e}")
            raise
    
    def consume_messages(self):
        """
        Consume messages from Kafka
        
        Yields:
            KafkaMessage objects
        """
        if not self._consumer:
            raise RuntimeError("Kafka consumer not initialized")
        
        try:
            for message in self._consumer:
                yield KafkaMessage(
                    topic=message.topic,
                    key=message.key.decode('utf-8') if message.key else "",
                    value=message.value,
                    partition=message.partition,
                    offset=message.offset
                )
        except Exception as e:
            logger.error(f"Error consuming messages: {e}")
            raise
    
    def close(self) -> None:
        """Close Kafka connections"""
        try:
            if self._producer:
                self._producer.close()
                logger.info("Kafka producer closed")
            
            if self._consumer:
                self._consumer.close()
                logger.info("Kafka consumer closed")
        except Exception as e:
            logger.error(f"Error closing Kafka connections: {e}")
