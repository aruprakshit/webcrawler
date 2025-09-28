# Web Crawler Database Schema

This document defines the complete database schema for the web crawler system. Both Python producer and Node.js consumer must use this exact schema.

## Keyspace
- **Name**: `webcrawler`
- **Replication**: SimpleStrategy with replication_factor = 1

## Tables

### 1. `urls` Table
**Purpose**: Tracks all discovered and crawled URLs

| Column | Type | Primary Key | Description |
|--------|------|-------------|-------------|
| `url_hash` | text | ✅ | MD5 hash of the URL (primary key) |
| `url` | text | ❌ | Full URL |
| `domain` | text | ❌ | Domain name (e.g., "example.com") |
| `status` | text | ❌ | URL status: 'discovered', 'crawled', 'failed' |
| `content_id` | text | ❌ | MinIO object ID for stored content |
| `discovered_at` | timestamp | ❌ | When URL was first discovered |
| `last_crawled` | timestamp | ❌ | When URL was last crawled |

**Indexes**:
- `urls_domain_idx` on `domain`
- `urls_status_idx` on `status`
- `urls_discovered_at_idx` on `discovered_at`

### 2. `domains` Table
**Purpose**: Tracks domain-specific information

| Column | Type | Primary Key | Description |
|--------|------|-------------|-------------|
| `domain` | text | ✅ | Domain name (e.g., "example.com") |
| `robots_txt` | text | ❌ | Cached robots.txt content |
| `robots_txt_updated` | timestamp | ❌ | When robots.txt was last fetched |
| `crawl_delay` | int | ❌ | Crawl delay in milliseconds |
| `last_crawled` | timestamp | ❌ | When domain was last crawled |

## Operations by Service

### Python Producer Operations
- **INSERT**: New URLs discovered
- **SELECT**: Check if URL already seen
- **UPDATE**: Mark URL as seen

### Node.js Consumer Operations
- **UPDATE**: Update URL status and content_id after crawling
- **SELECT**: Check URL status before crawling

## Status Values
- `discovered`: URL has been discovered but not yet crawled
- `crawled`: URL has been successfully crawled
- `failed`: URL crawling failed

## Content ID Format
- **Pattern**: `{timestamp}-{urlHash}.html`
- **Example**: `1738065832117-a1b2c3d4.html`
- **Purpose**: Links to MinIO object storage

## CQL Commands for Schema Management

### Schema Creation Commands
```sql
-- Create keyspace
CREATE KEYSPACE IF NOT EXISTS webcrawler
WITH REPLICATION = {'class': 'SimpleStrategy', 'replication_factor': 1};

-- Use keyspace
USE webcrawler;

-- Create urls table
CREATE TABLE IF NOT EXISTS urls (
    url_hash text PRIMARY KEY,
    url text,
    domain text,
    status text,
    content_id text,
    discovered_at timestamp,
    last_crawled timestamp
);

-- Create domains table
CREATE TABLE IF NOT EXISTS domains (
    domain text PRIMARY KEY,
    robots_txt text,
    robots_txt_updated timestamp,
    crawl_delay int,
    last_crawled timestamp
);

-- Create indexes
CREATE INDEX IF NOT EXISTS urls_domain_idx ON urls (domain);
CREATE INDEX IF NOT EXISTS urls_status_idx ON urls (status);
CREATE INDEX IF NOT EXISTS urls_discovered_at_idx ON urls (discovered_at);
```

### Schema Verification Commands
```sql
-- List all keyspaces
DESCRIBE KEYSPACES;

-- List tables in webcrawler keyspace
USE webcrawler;
DESCRIBE TABLES;

-- Describe specific table structure
DESCRIBE TABLE urls;
DESCRIBE TABLE domains;

-- Check table data
SELECT * FROM urls LIMIT 10;
SELECT * FROM domains LIMIT 10;

-- Check indexes
DESCRIBE INDEX urls_domain_idx;
DESCRIBE INDEX urls_status_idx;
DESCRIBE INDEX urls_discovered_at_idx;
```

### Schema Management Commands
```sql
-- Check if keyspace exists
SELECT keyspace_name FROM system_schema.keyspaces WHERE keyspace_name = 'webcrawler';

-- Check table metadata
SELECT table_name FROM system_schema.tables WHERE keyspace_name = 'webcrawler';

-- Check column information
SELECT column_name, type FROM system_schema.columns WHERE keyspace_name = 'webcrawler' AND table_name = 'urls';

-- Check index information
SELECT index_name FROM system_schema.indexes WHERE keyspace_name = 'webcrawler';
```

### Data Operations Commands
```sql
-- Insert new URL
INSERT INTO urls (url_hash, url, domain, status, discovered_at) 
VALUES ('abc123', 'https://example.com/page', 'example.com', 'discovered', toTimestamp(now()));

-- Update URL status after crawling
UPDATE urls 
SET status = 'crawled', last_crawled = toTimestamp(now()), content_id = 'content123' 
WHERE url_hash = 'abc123';

-- Check if URL exists
SELECT url_hash FROM urls WHERE url_hash = 'abc123';

-- Get URLs by domain
SELECT url, status FROM urls WHERE domain = 'example.com';

-- Get URLs by status
SELECT url, domain FROM urls WHERE status = 'discovered';

-- Insert/Update domain information
INSERT INTO domains (domain, robots_txt, robots_txt_updated, crawl_delay) 
VALUES ('example.com', 'User-agent: *\nDisallow: /admin/', toTimestamp(now()), 1000);

-- Update domain crawl information
UPDATE domains 
SET last_crawled = toTimestamp(now()) 
WHERE domain = 'example.com';
```

### Troubleshooting Commands
```sql
-- Check for missing columns (if schema is incomplete)
SELECT column_name FROM system_schema.columns 
WHERE keyspace_name = 'webcrawler' AND table_name = 'urls';

-- Verify all required columns exist
SELECT column_name FROM system_schema.columns 
WHERE keyspace_name = 'webcrawler' AND table_name = 'urls' 
AND column_name IN ('url_hash', 'url', 'domain', 'status', 'content_id', 'discovered_at', 'last_crawled');

-- Check table statistics
SELECT table_name, estimated_rows FROM system_schema.tables 
WHERE keyspace_name = 'webcrawler';

-- Check for any errors in system logs
SELECT * FROM system.logs WHERE level = 'ERROR' LIMIT 10;
```

### Docker Container Commands
```bash
# Connect to Cassandra container
docker compose exec cassandra cqlsh

# Run schema file directly
docker compose exec cassandra cqlsh -f /app/cassandra-schema.sql

# Check if schema was created
docker compose exec cassandra cqlsh -e "DESCRIBE KEYSPACES;"

# Verify webcrawler keyspace
docker compose exec cassandra cqlsh -e "USE webcrawler; DESCRIBE TABLES;"

# Check specific table structure
docker compose exec cassandra cqlsh -e "USE webcrawler; DESCRIBE TABLE urls;"
```

### Schema Validation Checklist
```sql
-- 1. Verify keyspace exists
SELECT keyspace_name FROM system_schema.keyspaces WHERE keyspace_name = 'webcrawler';

-- 2. Verify tables exist
SELECT table_name FROM system_schema.tables WHERE keyspace_name = 'webcrawler';

-- 3. Verify urls table has all columns
SELECT column_name FROM system_schema.columns 
WHERE keyspace_name = 'webcrawler' AND table_name = 'urls' 
ORDER BY column_name;

-- 4. Verify domains table has all columns
SELECT column_name FROM system_schema.columns 
WHERE keyspace_name = 'webcrawler' AND table_name = 'domains' 
ORDER BY column_name;

-- 5. Verify indexes exist
SELECT index_name FROM system_schema.indexes WHERE keyspace_name = 'webcrawler';
```
