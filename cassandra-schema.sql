-- Web Crawler Cassandra Schema
-- This file defines the complete database schema for the web crawler system

-- Create keyspace
CREATE KEYSPACE IF NOT EXISTS webcrawler 
WITH REPLICATION = {'class': 'SimpleStrategy', 'replication_factor': 1};

-- Use keyspace
USE webcrawler;

-- URLs table - tracks all discovered and crawled URLs
CREATE TABLE IF NOT EXISTS urls (
    url_hash text PRIMARY KEY,           -- MD5 hash of the URL (primary key)
    url text,                             -- Full URL
    domain text,                          -- Domain name (e.g., "example.com")
    status text,                          -- URL status: 'discovered', 'crawled', 'failed'
    content_id text,                      -- MinIO object ID for stored content
    discovered_at timestamp,              -- When URL was first discovered
    last_crawled timestamp                -- When URL was last crawled
);

-- Domains table - tracks domain-specific information
CREATE TABLE IF NOT EXISTS domains (
    domain text PRIMARY KEY,              -- Domain name (e.g., "example.com")
    robots_txt text,                      -- Cached robots.txt content
    robots_txt_updated timestamp,        -- When robots.txt was last fetched
    crawl_delay int,                      -- Crawl delay in milliseconds
    last_crawled timestamp                -- When domain was last crawled
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS urls_domain_idx ON urls (domain);
CREATE INDEX IF NOT EXISTS urls_status_idx ON urls (status);
CREATE INDEX IF NOT EXISTS urls_discovered_at_idx ON urls (discovered_at);
