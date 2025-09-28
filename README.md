#Web Crawler System

A scalable, distributed web crawler system built with Python (producer) and Node.js (consumer), using Kafka for message queuing, MinIO for object storage, Redis for caching, and Cassandra for metadata storage.

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Seed URLs     │    │   Python        │    │   Node.js       │
│                 │───▶│   Producer      │───▶│   Consumer      │
└─────────────────┘    │                 │    │                 │
                       │ • URL Discovery │    │ • Web Crawling  │
                       │ • HTML Parsing  │    │ • Content Store │
                       │ • Normalization │    │ • Rate Limiting │
                       └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │     Kafka       │    │     MinIO       │
                       │  (Message Queue)│    │ (Object Storage)│
                       └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │     Redis       │    │    Cassandra    │
                       │   (Caching)     │    │   (Metadata)    │
                       └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- At least 4GB RAM available
- Ports 3000, 3001, 6379, 8000, 9000, 9001, 9042, 9090, 9092 available

### Installation

1. **Clone and navigate to the project:**
   ```bash
   cd /home/hno3/system-designs/webcrawler
   ```

2. **Start the system:**
   ```bash
   ./start.sh
   ```

3. **Access the services:**
   - **Grafana Dashboard**: http://localhost:3000 (admin/admin123)
   - **Prometheus Metrics**: http://localhost:9090
   - **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin123)
   - **Application Health**: 
     - Python Producer: http://localhost:8000/health
     - Node.js Consumer: http://localhost:3001/health

## 🏭 System Components

### Python Producer Service
- **Purpose**: URL discovery, HTML parsing, and link extraction
- **Technologies**: Python 3.11, BeautifulSoup, Kafka, Redis, Cassandra
- **Features**:
  - HTML content parsing with BeautifulSoup
  - URL normalization and validation
  - Bloom filter for duplicate detection
  - Robots.txt caching with Redis
  - Prometheus metrics integration

### Node.js Consumer Service
- **Purpose**: Web page downloading and content storage
- **Technologies**: Node.js 18, Axios, MinIO, Kafka, Redis
- **Features**:
  - Concurrent HTTP requests with rate limiting
  - S3-compatible object storage with MinIO
  - Circuit breaker pattern for failing domains
  - Async/await for high concurrency
  - Health checks and monitoring

### Infrastructure Services

#### Kafka (Message Queue)
- **Topic**: `urls-to-crawl` - URLs waiting to be crawled
- **Partitioning**: By domain for politeness enforcement
- **Back-pressure**: Handles producer/consumer speed differences

#### MinIO (Object Storage)
- **S3-compatible**: Easy migration to AWS S3 later
- **Bucket**: `webcrawler-content`
- **Metadata**: Original URL, crawl timestamp, content type

#### Redis (Caching)
- **Robots.txt caching**: 24-hour TTL
- **Session storage**: Fast lookups
- **Rate limiting**: Domain-based delays

#### Cassandra (Metadata)
- **URL tracking**: Status, timestamps, content IDs
- **Domain management**: Crawl delays, robots.txt rules
- **Scalable**: Handles billions of URLs

## 📊 Monitoring & Observability

### Metrics (Prometheus)
- **URLs Processed**: Total URLs discovered by producer
- **URLs Crawled**: Successfully downloaded pages
- **Crawl Duration**: Time per URL download
- **Content Size**: Size distribution of downloaded content
- **Error Rates**: Failed crawls by domain

### Dashboards (Grafana)
- **System Overview**: Service health and performance
- **Crawl Statistics**: URLs processed, success rates
- **Resource Usage**: CPU, memory, disk usage
- **Error Analysis**: Failed crawls and error patterns

### Health Checks
- **Python Producer**: `GET /health` on port 8000
- **Node.js Consumer**: `GET /health` on port 3001
- **Docker Health**: Built-in container health checks

## 🔧 Configuration

### Environment Variables
```bash
# Kafka
KAFKA_BOOTSTRAP_SERVERS=kafka:9092

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# MinIO
MINIO_ENDPOINT=minio
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123

# Cassandra
CASSANDRA_HOST=cassandra
CASSANDRA_PORT=9042
```

### Scaling Configuration
- **Concurrent Requests**: `MAX_CONCURRENT_REQUESTS=10`
- **Crawl Delay**: `CRAWL_DELAY_MS=1000`
- **Request Timeout**: `REQUEST_TIMEOUT_MS=30000`

## 🚀 Horizontal Scaling

### Quick Scaling Commands

#### **Scale Node.js Consumer (Web Crawling)**
```bash
# Scale to 3 consumer instances for 3x crawling speed
docker compose up -d --scale nodejs-consumer=3

# Scale to 5 consumer instances for maximum throughput
docker compose up -d --scale nodejs-consumer=5

# Check running instances
docker compose ps | grep nodejs-consumer
```

#### **Scale Python Producer (URL Discovery)**
```bash
# Scale to 3 producer instances for 3x URL discovery
docker compose up -d --scale python-producer=3

# Scale to 2 producer instances (balanced approach)
docker compose up -d --scale python-producer=2

# Check running instances
docker compose ps | grep python-producer
```

#### **Scale Both Services Simultaneously**
```bash
# Scale both services for maximum performance
docker compose up -d --scale python-producer=3 --scale nodejs-consumer=5

# Check all scaled instances
docker compose ps
```

### How Scaling Works

#### **Kafka Partition Assignment**
- **3 Partitions per Topic**: `urls-to-crawl` and `crawled-content` each have 3 partitions
- **Automatic Load Balancing**: Kafka automatically assigns partitions to consumers
- **No Code Changes**: Your existing code works with multiple instances

#### **Partition Distribution Example**
```
With 3 Node.js Consumers:
├── Consumer 1 → Partition 0 of urls-to-crawl
├── Consumer 2 → Partition 1 of urls-to-crawl  
└── Consumer 3 → Partition 2 of urls-to-crawl

With 3 Python Producers:
├── Producer 1 → Can send to any partition
├── Producer 2 → Can send to any partition
└── Producer 3 → Can send to any partition
```

### Performance Benefits

#### **3x Node.js Consumers**
- **3x Crawling Speed**: Process 3 URLs simultaneously
- **Parallel Processing**: No waiting for single consumer
- **Fault Tolerance**: If 1 consumer fails, 2 continue working

#### **3x Python Producers**
- **3x URL Discovery**: Discover URLs from 3 sources simultaneously
- **Load Distribution**: Even workload across all producers
- **High Availability**: Multiple producers ensure continuous operation

### Monitoring Scaled Services

#### **Check Consumer Groups**
```bash
# List all consumer groups
docker compose exec kafka kafka-consumer-groups --bootstrap-server localhost:9092 --list

# Check partition assignment for your consumer group
docker compose exec kafka kafka-consumer-groups --bootstrap-server localhost:9092 --describe --group url-consumer-group
```

#### **Expected Output with 3 Consumers**
```
GROUP           TOPIC           PARTITION  CURRENT-OFFSET  LAG
url-consumer-group  urls-to-crawl  0          100           0
url-consumer-group  urls-to-crawl  1          100           0  
url-consumer-group  urls-to-crawl  2          100           0
```

#### **Monitor Service Health**
```bash
# Check all consumer health endpoints
curl http://localhost:3001/health  # Consumer 1
curl http://localhost:3002/health  # Consumer 2 (if scaled)
curl http://localhost:3003/health  # Consumer 3 (if scaled)

# Check all producer health endpoints
curl http://localhost:8000/health  # Producer 1
curl http://localhost:8001/health  # Producer 2 (if scaled)
curl http://localhost:8002/health  # Producer 3 (if scaled)
```

### Scaling Strategies

#### **Conservative Scaling (Recommended for Start)**
```bash
# Start with 2 consumers for 2x performance
docker compose up -d --scale nodejs-consumer=2
```

#### **Aggressive Scaling (Maximum Performance)**
```bash
# Scale to match partition count for optimal performance
docker compose up -d --scale nodejs-consumer=3 --scale python-producer=3
```

#### **Over-Scaling (High Availability)**
```bash
# Scale beyond partition count for redundancy
docker compose up -d --scale nodejs-consumer=5 --scale python-producer=3
```

### Scaling Best Practices

#### **1. Start Small, Scale Gradually**
```bash
# Start with 1 instance
docker compose up -d

# Scale to 2 instances
docker compose up -d --scale nodejs-consumer=2

# Monitor performance, then scale to 3
docker compose up -d --scale nodejs-consumer=3
```

#### **2. Monitor Resource Usage**
```bash
# Check container resource usage
docker stats

# Monitor Kafka partition assignment
docker compose exec kafka kafka-consumer-groups --bootstrap-server localhost:9092 --describe --group url-consumer-group
```

#### **3. Scale Based on Load**
- **Low Load**: 1-2 consumers
- **Medium Load**: 3 consumers (matches partition count)
- **High Load**: 3+ consumers (with some idle for redundancy)

### Troubleshooting Scaled Services

#### **Check if Scaling Worked**
```bash
# Verify all instances are running
docker compose ps

# Check logs for all instances
docker compose logs nodejs-consumer
docker compose logs python-producer
```

#### **Common Scaling Issues**

1. **Port Conflicts**: Each scaled instance needs unique ports
   ```bash
   # Check if ports are available
   netstat -tulpn | grep :3001
   ```

2. **Resource Limits**: Too many instances can exhaust resources
   ```bash
   # Monitor system resources
   docker stats
   ```

3. **Kafka Partition Assignment**: Ensure consumers are assigned to different partitions
   ```bash
   # Check partition assignment
   docker compose exec kafka kafka-consumer-groups --bootstrap-server localhost:9092 --describe --group url-consumer-group
   ```

### Scaling Configuration Options

#### **Environment Variables for Scaling**
```bash
# Set in docker-compose.yml or .env file
MAX_CONCURRENT_REQUESTS=10  # Per consumer instance
CRAWL_DELAY_MS=1000        # Delay between requests
REQUEST_TIMEOUT_MS=30000   # Timeout per request
```

#### **Docker Compose Scaling Limits**
```yaml
# Add to docker-compose.yml for automatic scaling
deploy:
  replicas: 3  # Default number of instances
  resources:
    limits:
      cpus: '0.5'
      memory: 512M
    reservations:
      cpus: '0.25'
      memory: 256M
```

## 🛠️ Development

### Local Development
```bash
# Start only infrastructure
docker-compose up -d kafka redis cassandra minio

# Run services locally
cd python-producer && python main.py
cd nodejs-consumer && npm start
```

### Adding New Features
1. **URL Filters**: Add domain blacklists in `python-producer/main.py`
2. **Content Processing**: Extend parsing logic in `nodejs-consumer/main.js`
3. **Custom Metrics**: Add Prometheus counters in both services
4. **Storage Backends**: Implement additional storage adapters

### Testing
```bash
# Run tests
docker-compose exec python-producer python -m pytest
docker-compose exec nodejs-consumer npm test

# Load testing
docker-compose exec kafka kafka-producer-perf-test \
  --topic urls-to-crawl \
  --num-records 1000 \
  --record-size 100
```

## 📈 Performance Characteristics

### Throughput
- **Target**: 400 pages/second (1 billion pages in 30 days)
- **Bottlenecks**: Network I/O, robots.txt checks
- **Scaling**: Horizontal scaling of consumer workers

### Storage Requirements
- **Content**: 100 TB for 1 billion pages (100 KB average)
- **Metadata**: 200 GB for URL tracking
- **Cache**: 20 GB for robots.txt files

### Memory Usage
- **Bloom Filter**: 1.2 GB for 1 billion URLs
- **Redis Cache**: 20 GB for robots.txt
- **Application**: 512 MB per worker

## 🔒 Security & Best Practices

### Politeness
- **Robots.txt Compliance**: Automatic checking and caching
- **Rate Limiting**: Domain-based crawl delays
- **User-Agent**: Identifiable crawler identification

### Non-Root Execution
- **Docker Containers**: All services run as UID/GID 1000
- **File Permissions**: Proper ownership of data volumes
- **Security**: Reduced attack surface

### Data Privacy
- **Content Storage**: Encrypted at rest (MinIO)
- **Metadata**: Secure Cassandra connections
- **Logs**: No sensitive data in application logs

## 🚨 Troubleshooting

### Common Issues

1. **Services won't start**:
   ```bash
   docker-compose logs [service-name]
   ```

2. **Kafka connection issues**:
   ```bash
   docker-compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list
   ```

3. **MinIO access denied**:
   - Check credentials in `.env` file
   - Verify bucket exists: http://localhost:9001

4. **High memory usage**:
   - Reduce `MAX_CONCURRENT_REQUESTS`
   - Increase `CRAWL_DELAY_MS`
   - Scale horizontally

### Performance Tuning

1. **Increase throughput**:
   - Add more consumer workers
   - Optimize Kafka partitions
   - Tune Redis cache size

2. **Reduce latency**:
   - Decrease crawl delays
   - Optimize database queries
   - Use connection pooling

## 📚 Further Reading

- [System Design Template](../template.txt)
- [Original Design Plan](./plan.txt)
- [Questions & Answers](./questions.txt)
- [Kafka Documentation](https://kafka.apache.org/documentation/)
- [MinIO Documentation](https://docs.min.io/)
- [Cassandra Documentation](https://cassandra.apache.org/doc/)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.
