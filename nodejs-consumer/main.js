#!/usr/bin/env node
/**
 * Web Crawler Consumer Service
 * Handles web page downloading and content storage
 */

const { Kafka } = require('kafkajs');
const axios = require('axios');
const cheerio = require('cheerio');
const Minio = require('minio');
const Redis = require('redis');
const cassandra = require('cassandra-driver');
const prometheus = require('prom-client');
const winston = require('winston');
const pLimit = require('p-limit');

// Configure logging
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console(),
    new winston.transports.File({ filename: 'consumer.log' })
  ]
});

// Prometheus metrics
const register = new prometheus.Registry();
prometheus.collectDefaultMetrics({ register });

const urlsCrawled = new prometheus.Counter({
  name: 'urls_crawled_total',
  help: 'Total number of URLs crawled',
  registers: [register]
});

const urlsFailed = new prometheus.Counter({
  name: 'urls_failed_total',
  help: 'Total number of URLs that failed to crawl',
  registers: [register]
});

const crawlDuration = new prometheus.Histogram({
  name: 'crawl_duration_seconds',
  help: 'Time spent crawling a single URL',
  buckets: [0.1, 0.5, 1, 2, 5, 10, 30],
  registers: [register]
});

const contentSize = new prometheus.Histogram({
  name: 'content_size_bytes',
  help: 'Size of downloaded content in bytes',
  buckets: [1024, 10240, 102400, 1048576, 10485760],
  registers: [register]
});

class WebCrawlerConsumer {
  constructor() {
    this.kafka = null;
    this.consumer = null;
    this.minioClient = null;
    this.redisClient = null;
    this.cassandraClient = null;
    this.httpClient = null;
    this.concurrencyLimit = pLimit(10); // Limit concurrent requests
  }

  async initialize() {
    logger.info('Initializing Web Crawler Consumer...');

    // Kafka consumer
    this.kafka = Kafka({
      clientId: 'webcrawler-consumer',
      brokers: (process.env.KAFKA_BOOTSTRAP_SERVERS || 'localhost:9092').split(',')
    });

    this.consumer = this.kafka.consumer({ groupId: 'webcrawler-group' });

    // MinIO client
    this.minioClient = new Minio.Client({
      endPoint: process.env.MINIO_ENDPOINT || 'localhost',
      port: parseInt(process.env.MINIO_PORT || '9000'),
      useSSL: false,
      accessKey: process.env.MINIO_ACCESS_KEY || 'minioadmin',
      secretKey: process.env.MINIO_SECRET_KEY || 'minioadmin123'
    });

    // Redis client
    this.redisClient = Redis.createClient({
      host: process.env.REDIS_HOST || 'localhost',
      port: parseInt(process.env.REDIS_PORT || '6379')
    });

    await this.redisClient.connect();

    // Cassandra client
    this.cassandraClient = new cassandra.Client({
      contactPoints: [(process.env.CASSANDRA_HOST || 'localhost')],
      localDataCenter: 'datacenter1',
      keyspace: 'webcrawler'
    });

    // HTTP client with retry logic
    this.httpClient = axios.create({
      timeout: 30000,
      maxRedirects: 5,
      headers: {
        'User-Agent': 'WebCrawler/1.0 (https://example.com/bot)'
      }
    });

    // Initialize MinIO bucket
    await this.initializeMinIO();

    logger.info('Web Crawler Consumer initialized successfully');
  }

  async initializeMinIO() {
    try {
      const bucketName = 'webcrawler-content';
      const exists = await this.minioClient.bucketExists(bucketName);
      if (!exists) {
        await this.minioClient.makeBucket(bucketName, 'us-east-1');
        logger.info(`Created MinIO bucket: ${bucketName}`);
      }
    } catch (error) {
      logger.error('Failed to initialize MinIO:', error);
      throw error;
    }
  }

  async getRobotsTxtRules(domain) {
    try {
      // Check Redis cache first
      const cacheKey = `robots:${domain}`;
      const cached = await this.redisClient.get(cacheKey);
      
      if (cached) {
        return JSON.parse(cached);
      }

      // Fetch robots.txt
      const robotsUrl = `http://${domain}/robots.txt`;
      const response = await this.httpClient.get(robotsUrl);
      
      // Parse robots.txt (simplified)
      const rules = this.parseRobotsTxt(response.data);
      
      // Cache for 24 hours
      await this.redisClient.setEx(cacheKey, 86400, JSON.stringify(rules));
      
      return rules;
    } catch (error) {
      logger.warn(`Failed to get robots.txt for ${domain}:`, error.message);
      return { allowed: true, delay: 1000 }; // Default: allow with 1s delay
    }
  }

  parseRobotsTxt(content) {
    const lines = content.split('\n');
    let inUserAgent = false;
    let allowed = true;
    let delay = 1000;

    for (const line of lines) {
      const trimmed = line.trim().toLowerCase();
      
      if (trimmed.startsWith('user-agent:')) {
        const userAgent = trimmed.substring(11).trim();
        inUserAgent = userAgent === '*' || userAgent.includes('webcrawler');
      } else if (inUserAgent && trimmed.startsWith('disallow:')) {
        allowed = false;
      } else if (inUserAgent && trimmed.startsWith('crawl-delay:')) {
        delay = parseInt(trimmed.substring(12).trim()) * 1000;
      }
    }

    return { allowed, delay };
  }

  async crawlUrl(url) {
    const startTime = Date.now();
    
    try {
      logger.info(`Crawling URL: ${url}`);
      
      // Extract domain for robots.txt check
      const domain = new URL(url).hostname;
      const rules = await this.getRobotsTxtRules(domain);
      
      if (!rules.allowed) {
        logger.info(`URL ${url} blocked by robots.txt`);
        return null;
      }

      // Respect crawl delay
      if (rules.delay > 0) {
        await new Promise(resolve => setTimeout(resolve, rules.delay));
      }

      // Download the page
      const response = await this.httpClient.get(url);
      const content = response.data;
      const contentType = response.headers['content-type'] || 'text/html';
      
      // Only process HTML content
      if (!contentType.includes('text/html')) {
        logger.info(`Skipping non-HTML content: ${url}`);
        return null;
      }

      // Store content in MinIO
      const contentId = this.generateContentId(url);
      await this.minioClient.putObject(
        'webcrawler-content',
        contentId,
        content,
        {
          'Content-Type': contentType,
          'X-Original-URL': url,
          'X-Crawled-At': new Date().toISOString()
        }
      );

      // Update metrics
      urlsCrawled.inc();
      crawlDuration.observe((Date.now() - startTime) / 1000);
      contentSize.observe(Buffer.byteLength(content, 'utf8'));

      // Update Cassandra
      await this.updateUrlStatus(url, domain, 'crawled', contentId);

      logger.info(`Successfully crawled: ${url}`);
      
      return {
        url,
        domain,
        content,
        contentId,
        contentType
      };

    } catch (error) {
      urlsFailed.inc();
      logger.error(`Failed to crawl ${url}:`, error.message);
      
      // Update status in Cassandra
      await this.updateUrlStatus(url, new URL(url).hostname, 'failed');
      
      return null;
    }
  }

  generateContentId(url) {
    const timestamp = Date.now();
    const urlHash = require('crypto')
      .createHash('md5')
      .update(url)
      .digest('hex')
      .substring(0, 8);
    return `${timestamp}-${urlHash}.html`;
  }

  async updateUrlStatus(url, domain, status, contentId = null) {
    try {
      const urlHash = require('crypto')
        .createHash('md5')
        .update(url)
        .digest('hex');
      
      const query = `
        UPDATE urls 
        SET status = ?, last_crawled = toTimestamp(now())${contentId ? ', content_id = ?' : ''}
        WHERE url_hash = ?
      `;
      
      const params = contentId 
        ? [status, contentId, urlHash]
        : [status, urlHash];
      
      await this.cassandraClient.execute(query, params);
    } catch (error) {
      logger.error('Failed to update URL status:', error);
    }
  }

  async processMessage(message) {
    const url = message.value.toString();
    
    return this.concurrencyLimit(async () => {
      return await this.crawlUrl(url);
    });
  }

  async run() {
    logger.info('Starting Web Crawler Consumer...');

    // Start metrics server
    const express = require('express');
    const app = express();
    
    app.get('/metrics', async (req, res) => {
      res.set('Content-Type', register.contentType);
      res.end(await register.metrics());
    });
    
    app.get('/health', (req, res) => {
      res.json({ status: 'healthy', timestamp: new Date().toISOString() });
    });
    
    app.listen(3001, () => {
      logger.info('Metrics server running on port 3001');
    });

    // Connect to Kafka
    await this.consumer.connect();
    await this.consumer.subscribe({ topic: 'urls-to-crawl', fromBeginning: false });

    // Start consuming messages
    await this.consumer.run({
      eachMessage: async ({ topic, partition, message }) => {
        try {
          await this.processMessage(message);
        } catch (error) {
          logger.error('Error processing message:', error);
        }
      }
    });

    logger.info('Web Crawler Consumer is running...');
  }

  async shutdown() {
    logger.info('Shutting down Web Crawler Consumer...');
    
    if (this.consumer) {
      await this.consumer.disconnect();
    }
    
    if (this.redisClient) {
      await this.redisClient.quit();
    }
    
    if (this.cassandraClient) {
      await this.cassandraClient.shutdown();
    }
  }
}

// Graceful shutdown handling
process.on('SIGINT', async () => {
  logger.info('Received SIGINT, shutting down gracefully...');
  if (global.crawlerConsumer) {
    await global.crawlerConsumer.shutdown();
  }
  process.exit(0);
});

process.on('SIGTERM', async () => {
  logger.info('Received SIGTERM, shutting down gracefully...');
  if (global.crawlerConsumer) {
    await global.crawlerConsumer.shutdown();
  }
  process.exit(0);
});

// Main execution
async function main() {
  const consumer = new WebCrawlerConsumer();
  global.crawlerConsumer = consumer;
  
  try {
    await consumer.initialize();
    await consumer.run();
  } catch (error) {
    logger.error('Fatal error:', error);
    process.exit(1);
  }
}

if (require.main === module) {
  main().catch(console.error);
}

module.exports = WebCrawlerConsumer;
