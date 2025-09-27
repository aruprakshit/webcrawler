#!/bin/bash

# Web Crawler Startup Script

set -e

echo "🚀 Starting Web Crawler System..."

# Check if Docker and Docker Compose are installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating environment file from template..."
    cp env.example .env
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data/{kafka,redis,minio,cassandra,prometheus,grafana}

# Set proper permissions for non-root user (UID/GID 1001)
echo "🔐 Setting permissions..."
sudo chown -R 1001:1001 data/

# Start infrastructure services first
echo "🏗️  Starting infrastructure services..."
docker-compose up -d zookeeper kafka redis cassandra minio

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Check if Kafka is ready
echo "🔍 Checking Kafka readiness..."
timeout 60 bash -c 'until docker-compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list; do sleep 2; done'

# Create Kafka topics
echo "📋 Creating Kafka topics..."
docker-compose exec kafka kafka-topics --bootstrap-server localhost:9092 --create --topic urls-to-crawl --partitions 3 --replication-factor 1 || true
docker-compose exec kafka kafka-topics --bootstrap-server localhost:9092 --create --topic crawled-content --partitions 3 --replication-factor 1 || true

# Start application services
echo "🚀 Starting application services..."
docker-compose up -d python-producer nodejs-consumer

# Start monitoring services
echo "📊 Starting monitoring services..."
docker-compose up -d prometheus grafana kafka-ui

# Wait for all services to be ready
echo "⏳ Waiting for all services to be ready..."
sleep 20

# Display service status
echo "📋 Service Status:"
docker-compose ps

# Display access information
echo ""
echo "🎉 Web Crawler System is running!"
echo ""
echo "📊 Monitoring:"
echo "  - Prometheus: http://localhost:9090"
echo "  - Grafana: http://localhost:3000 (admin/admin123)"
echo "  - Kafka UI: http://localhost:8080"
echo ""
echo "🗄️  Storage:"
echo "  - MinIO Console: http://localhost:9001 (minioadmin/minioadmin123)"
echo ""
echo "🔍 Application Health:"
echo "  - Python Producer: http://localhost:8000/health"
echo "  - Node.js Consumer: http://localhost:3001/health"
echo ""
echo "📝 Logs:"
echo "  - View all logs: docker-compose logs -f"
echo "  - Python Producer: docker-compose logs -f python-producer"
echo "  - Node.js Consumer: docker-compose logs -f nodejs-consumer"
echo ""
echo "🛑 To stop the system: docker-compose down"
